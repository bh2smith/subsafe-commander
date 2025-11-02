mod dune;
mod environment;
mod log_setup;
mod multisend;
mod ops;
mod safe;
mod utils;

use alloy::primitives::{Address, Bytes, U256};
use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::str::FromStr;

use dune::DuneClient;
use environment::Config;
use multisend::{MultiSendTx, partition_transactions};
use ops::{
    add_owner::{AddOwnerArgs, build_add_owner_with_threshold},
    airdrop::transactions_for as airdrop_transactions,
    snapshot::{SnapshotCommand, transactions_for as snapshot_transactions},
};

use crate::{
    multisend::{MULTISEND_CONTRACT, build_encoded_multisend},
    safe::{
        api::post_safe_tx,
        tx::{SafeTransaction, get_safe_nonce},
    },
};

/// Supported commands for the SubSafe Commander
#[derive(Debug, Clone, Subcommand)]
enum Command {
    /// Claim SAFE airdrop
    Claim,

    /// Add an owner to sub-safes
    AddOwner {
        /// New owner address (required)
        #[arg(long)]
        new_owner: String,

        /// Signature threshold (default: 1)
        #[arg(long, default_value = "1")]
        threshold: u64,
    },

    /// Set delegate for snapshot voting
    SetDelegate {
        /// Delegate address (defaults to parent if omitted)
        #[arg(long)]
        delegate: Option<String>,
    },

    /// Clear delegate for snapshot voting
    ClearDelegate,
}

/// SubSafe Commander - Control your fleet of Safes from the command line
#[derive(Parser, Debug)]
#[command(author, version, about)]
struct Args {
    /// Parent Safe address (owner of all sub-safes)
    #[arg(short, long, env = "PARENT_SAFE")]
    parent: String,

    /// Comma-separated list of sub-safe addresses (optional, will fetch from Dune if not provided)
    #[arg(short, long)]
    sub_safes: Option<String>,

    /// Index to start from in the list of children
    #[arg(long, default_value = "0")]
    index_from: i64,

    /// Number of safes to process
    #[arg(long, default_value = "1000")]
    num_safes: i64,

    /// Subcommand to execute
    #[command(subcommand)]
    command: Command,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logger
    log_setup::init_with_level(log::LevelFilter::Info);
    log::info!("SubSafe Commander (Rust) starting...");

    // Parse CLI arguments
    let args = Args::parse();

    // Load configuration
    let config = Config::from_env().await?;

    // Parse parent address
    let parent_address = Address::from_str(&args.parent)
        .with_context(|| format!("Invalid parent address: {}", args.parent))?;

    // Get children addresses
    let children_addresses = if let Some(sub_safes) = &args.sub_safes {
        // Parse from comma-separated list
        sub_safes
            .split(',')
            .map(|s| {
                Address::from_str(s.trim())
                    .with_context(|| format!("Invalid sub-safe address: {}", s))
            })
            .collect::<Result<Vec<_>>>()?
    } else {
        // Fetch from Dune
        let dune_api_key = config
            .dune_api_key
            .context("DUNE_API_KEY required when --sub-safes is not provided")?;

        let dune_client = DuneClient::new(dune_api_key);
        let index_to = args.index_from + args.num_safes;

        dune_client
            .fetch_child_safes(&args.parent, args.index_from, index_to)
            .await?
    };

    log::info!("Parent: {:?}", parent_address);
    log::info!("Processing {} child safe(s)", children_addresses.len());

    // Build transactions based on command
    let transactions: Vec<MultiSendTx> = match args.command {
        Command::Claim => {
            log::info!("Building CLAIM transactions");
            airdrop_transactions(parent_address, &children_addresses).await?
        }
        Command::AddOwner {
            new_owner,
            threshold,
        } => {
            let new_owner = Address::from_str(&new_owner)
                .with_context(|| format!("Invalid new owner address: {}", new_owner))?;
            log::info!("Building ADD_OWNER transactions for {:?}", new_owner);

            let add_owner_args = AddOwnerArgs::with_threshold(new_owner, threshold);
            children_addresses
                .iter()
                .map(|child| {
                    build_add_owner_with_threshold(parent_address, *child, &add_owner_args)
                })
                .collect::<Result<Vec<_>>>()?
        }
        Command::SetDelegate { delegate } => {
            log::info!("Building SET_DELEGATE transactions");

            let delegate = delegate
                .as_ref()
                .map(|s| Address::from_str(s))
                .transpose()
                .context("Invalid delegate address")?;
            snapshot_transactions(
                parent_address,
                &children_addresses,
                SnapshotCommand::SetDelegate,
                delegate,
            )?
        }
        Command::ClearDelegate => {
            log::info!("Building CLEAR_DELEGATE transactions");
            snapshot_transactions(
                parent_address,
                &children_addresses,
                SnapshotCommand::ClearDelegate,
                None,
            )?
        }
    };

    log::info!("Built {:#?} transaction(s)", transactions);

    if transactions.is_empty() {
        log::warn!("No transactions to execute");
        return Ok(());
    }

    // Partition if needed and display summary
    let partitions = partition_transactions(&transactions)?;
    log::info!(
        "Transactions will be executed in {} batch(es)",
        partitions.len()
    );

    let chain_id = U256::from(1); // mainnet; make configurable
    for (i, partition) in partitions.iter().enumerate() {
        log::info!("Batch {}: {} transaction(s)", i + 1, partition.len());

        // Encode multisend batch
        let encoded_multisend = build_encoded_multisend(partition)?;
        // TODO: fetch actual nonce.
        let nonce = get_safe_nonce(parent_address, &config._provider).await?;

        // Construct the Safe transaction (unsigned)
        let mut safe_tx = SafeTransaction::new(
            Address::from_str(MULTISEND_CONTRACT)?,
            U256::ZERO,
            encoded_multisend.clone(),
        )
        .with_nonce(nonce)
        .with_operation(safe::tx::SafeOperation::DelegateCall);

        // Compute Safe transaction hash
        let tx_hash = safe_tx.safe_tx_hash(parent_address, chain_id);
        let tx_hash_hex = format!("0x{}", hex::encode(tx_hash));

        if let Some(ref signer) = config.proposer {
            log::info!("🔏 Signing batch {} with proposer key...", i + 1);
            // Build + sign the multisend Safe transaction
            safe_tx.sign(parent_address, chain_id, signer)?;

            log::info!("✅ Built and signed Safe transaction.");
            log::info!("Transaction hash: {tx_hash_hex}");

            // Post it to the Safe Transaction Service
            post_safe_tx(
                &safe_tx,
                parent_address,
                &safe_tx.signatures_blob(),
                &Bytes::from(tx_hash.as_slice().to_vec()),
                signer.address(),
                // &config.safe_tx_service_url,
                "https://api.safe.global/tx-service/eth",
            )
            .await?;

            log::info!(
                "Transaction queue: https://app.safe.global/transactions/queue?safe=eth:{:?}",
                parent_address
            );
        } else {
            log::info!("Unsigned Safe transaction built:");
            log::info!(" - Batch: {}", i + 1);
            log::info!(" - Nonce: {}", nonce);
            log::info!(" - To: {:?}", safe_tx.to);
            log::info!(" - Operation: {:?}", safe_tx.operation);
            log::info!(" - Data: 0x{}", hex::encode(safe_tx.data));
            log::info!(" - SafeTx hash: {tx_hash_hex}");
            log::info!(
                "You can submit this manually via: https://app.safe.global/transactions/queue?safe=eth:{:?}",
                parent_address
            );
        }
    }

    log::info!("✓ All transactions prepared successfully");
    log::info!(
        "Note: Actual signing and submission requires integration with Safe Transaction Service"
    );

    Ok(())
}
