use alloy::{
    dyn_abi::DynSolValue,
    primitives::{Address, FixedBytes, U256},
};
use anyhow::{Context, Result};
use reqwest;
use serde::{Deserialize, Serialize};
use std::str::FromStr;

/// Allocation API base URL
const ALLOCATION_BASE_URL: &str = "https://safe-claiming-app-data.gnosis-safe.io/allocations";

/// Maximum U128 value for claiming all tokens
pub const MAX_U128: u128 = 340282366920938463463374607431768211455;

/// Represents Safe Airdrop Allocation Data
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Allocation {
    pub tag: String,
    pub account: String,
    pub chain_id: u64,
    pub contract: String,
    pub vesting_id: String,
    pub duration_weeks: u64,
    pub start_date: u64,
    pub amount: String,
    pub curve: u64,
    pub proof: Vec<String>,
}

impl Allocation {
    /// Returns API URL for a given address
    fn api_url(address: &str) -> String {
        let chain_id = 1; // Airdrop was only on mainnet
        format!("{}/{}/{}.json", ALLOCATION_BASE_URL, chain_id, address)
    }

    /// Fetches allocation data from the Safe Foundation API
    pub async fn from_address(safe_address: &str) -> Result<Vec<Allocation>> {
        let url = Self::api_url(safe_address);

        // Create a client that doesn't use system proxy (fixes macOS test issues)
        let client = reqwest::Client::builder()
            .no_proxy()
            .use_rustls_tls()
            .build()
            .context("Failed to create HTTP client")?;

        let response = client
            .get(&url)
            .send()
            .await
            .context("Failed to fetch allocation data")?;

        if !response.status().is_success() {
            let text = response.text().await?;
            if text.contains("NoSuchKey") {
                anyhow::bail!("{} is not eligible for SAFE airdrop", safe_address);
            }
            anyhow::bail!("Allocation request failed: {}", text);
        }

        let allocations: Vec<Allocation> = response
            .json()
            .await
            .context("Failed to parse allocation response")?;

        Ok(allocations)
    }

    pub fn encoded_claim_params(&self, beneficiary: &str) -> Result<Vec<DynSolValue>> {
        let vesting_id_bytes = if self.vesting_id.starts_with("0x") {
            alloy::hex::decode(&self.vesting_id[2..])
                .map_err(|e| anyhow::anyhow!("Invalid vesting ID hex: {}", e))?
        } else {
            alloy::hex::decode(&self.vesting_id)
                .map_err(|e| anyhow::anyhow!("Invalid vesting ID hex: {}", e))?
        };

        if vesting_id_bytes.len() != 32 {
            anyhow::bail!("Vesting ID must be 32 bytes");
        }

        let vesting_bytes_fixed = FixedBytes::<32>::from_slice(&vesting_id_bytes);
        let beneficiary_addr = Address::from_str(beneficiary)?;

        Ok(vec![
            DynSolValue::FixedBytes(vesting_bytes_fixed, 32),
            DynSolValue::Address(beneficiary_addr),
            DynSolValue::Uint(U256::from(MAX_U128), 128),
        ])
    }

    /// Get the airdrop contract address
    pub fn contract_address(&self) -> Result<Address> {
        Address::from_str(&self.contract)
            .with_context(|| format!("Invalid contract address: {}", self.contract))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_api_url() {
        let url = Allocation::api_url("0x3A11F4c84688a1264690d696D8D807a25Ee02dd2");
        assert_eq!(
            url,
            "https://safe-claiming-app-data.gnosis-safe.io/allocations/1/0x3A11F4c84688a1264690d696D8D807a25Ee02dd2.json"
        );
    }

    #[tokio::test]
    async fn test_allocation_from_address() {
        let alloc = Allocation::from_address("0x3A11F4c84688a1264690d696D8D807a25Ee02dd2")
            .await
            .unwrap();
        eprintln!("Allocations {:#?}", alloc);
        assert!(!alloc.is_empty());

        let alloc = Allocation::from_address("0x8F66b9DAC2E4eb07Da11DcbA76111b4677Dbac18")
            .await
            .unwrap();
        eprintln!("Allocations {:#?}", alloc);
        assert!(!alloc.is_empty());
    }

    #[test]
    fn test_max_u128() {
        assert_eq!(MAX_U128, u128::MAX);
    }
}
