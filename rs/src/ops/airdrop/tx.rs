use alloy::primitives::Address;
use anyhow::Result;

use crate::multisend::MultiSendTx;
use crate::ops::airdrop::{allocation::Allocation, encode::encode_claim};

/// Build transactions for claiming airdrops for all child safes
pub async fn transactions_for(
    parent_address: Address,
    children: &[Address],
) -> Result<Vec<MultiSendTx>> {
    log::info!("Using Parent Safe {:?} as Beneficiary", parent_address);

    let mut transactions = Vec::new();

    for child in children {
        let child_str = child.to_string();

        match Allocation::from_address(&child_str).await {
            Ok(allocations) => {
                log::info!(
                    "Found {} allocation(s) for child {:?}",
                    allocations.len(),
                    child
                );

                for allocation in allocations {
                    // Convert to lowercase for API compatibility
                    let parent_str = format!("{:?}", parent_address).to_lowercase();
                    match encode_claim(&allocation, &parent_str) {
                        Ok(tx) => transactions.push(tx.as_multisend(*child, &parent_address)?),
                        Err(e) => {
                            log::error!("Failed to build claim for child {:?}: {}", child, e);
                        }
                    }
                }
            }
            Err(e) => {
                log::warn!("No allocation found for child {:?}: {}", child, e);
            }
        }
    }

    log::info!("Built {} claim transaction(s)", transactions.len());
    Ok(transactions)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[tokio::test]
    async fn test_transactions_for() {
        let _ = env_logger::builder()
            .is_test(true)
            .filter_level(log::LevelFilter::Info)
            .try_init();
        let parent = Address::from_str("0x3A11F4c84688a1264690d696D8D807a25Ee02dd2").unwrap();
        let children: Vec<Address> =
            vec![Address::from_str("0x8F66b9DAC2E4eb07Da11DcbA76111b4677Dbac18").unwrap()];

        let txs = transactions_for(parent, &children).await.unwrap();
        assert!(txs.len() > 1);
    }
}
