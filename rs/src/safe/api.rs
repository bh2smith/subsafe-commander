use alloy::primitives::{Address, Bytes};
use anyhow::{Context, Result};
use serde::Serialize;
use std::io::{self, Write};

use crate::safe::tx::SafeTransaction;

/// The payload expected by the Safe Transaction Service
#[derive(Serialize, Debug)]
struct SafeTxPayload {
    safe: String,
    to: String,
    value: String,
    data: String,
    operation: u8,
    safe_tx_gas: String,
    base_gas: String,
    gas_price: String,
    gas_token: String,
    refund_receiver: String,
    nonce: String,
    contract_transaction_hash: String,
    sender: String,
    signature: String,
}

/// Posts a signed Safe transaction to the Safe Transaction Service.
/// Returns the nonce on success, -1 on failure.
pub async fn post_safe_tx(
    safe_tx: &SafeTransaction,
    safe_address: Address,
    signature: &Bytes,
    safe_tx_hash: &Bytes,
    sender_address: Address,
    safe_service_url: &str,
) -> Result<i64> {
    // 1. Basic signature presence check
    if signature.is_empty() {
        anyhow::bail!("Attempt to post unsigned transaction!");
    }

    // 2. Print transaction info
    log::info!(
        "posting transaction with hash 0x{} to {}",
        hex::encode(safe_tx_hash),
        safe_address
    );

    // 3. Confirm interactively
    print!("are you sure? (y/n) ");
    io::stdout().flush()?;
    let mut confirm = String::new();
    io::stdin().read_line(&mut confirm)?;
    if confirm.trim() != "y" {
        println!("aborted.");
        return Ok(-1);
    }

    // 4. Build payload
    let payload = SafeTxPayload {
        safe: safe_address.to_string(),
        to: safe_tx.to.to_string(),
        value: safe_tx.value.to_string(),
        data: hex::encode(&safe_tx.data),
        operation: safe_tx.operation as u8,
        safe_tx_gas: safe_tx.safe_tx_gas.to_string(),
        base_gas: safe_tx.base_gas.to_string(),
        gas_price: safe_tx.gas_price.to_string(),
        gas_token: safe_tx.gas_token.to_string(),
        refund_receiver: safe_tx.refund_receiver.to_string(),
        nonce: safe_tx.nonce.to_string(),
        contract_transaction_hash: format!("0x{}", hex::encode(safe_tx_hash)),
        sender: sender_address.to_string(),
        signature: format!("0x{}", hex::encode(signature)),
    };

    log::info!("Payload: {:#?}", payload);

    // 5. POST to Safe Transaction Service
    let endpoint = format!("{safe_service_url}/api/v1/safes/{safe_address}/multisig-transactions/");

    log::info!("Endpoint: {}", endpoint);
    // Create a client that doesn't use system proxy (fixes macOS test issues)
    let client = reqwest::Client::builder()
        .no_proxy()
        .use_rustls_tls()
        .build()
        .context("Failed to create HTTP client")?;
    let resp = client.post(&endpoint).json(&payload).send().await?;

    // 6. Handle response
    if resp.status().is_success() {
        println!("✅ Transaction posted successfully.");
        Ok(safe_tx.nonce.as_limbs()[0] as i64)
    } else {
        let text = resp.text().await?;
        eprintln!("❌ Safe Transaction Service error: {text}");
        Ok(-1)
    }
}
