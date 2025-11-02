use alloy::primitives::Address;
use anyhow::{Context, Result};
use duners::client::DuneClient as DunersClient;
use duners::parameters::Parameter;
use serde::Deserialize;
use std::str::FromStr;

/// Result row from Dune query for Safe families
/// Query 1416166 returns: index (number) and bracket (Address)
#[derive(Debug, Deserialize)]
struct SafeFamilyRow {
    // index: i64,
    bracket: String,
}

/// Dune API client wrapper for SubSafe Commander
pub struct DuneClient {
    client: DunersClient,
}

impl DuneClient {
    /// Create a new Dune client with an API key
    pub fn new(api_key: String) -> Self {
        Self {
            client: DunersClient::new(&api_key),
        }
    }

    /// Fetch child safes from parent via Dune query
    ///
    /// Uses Dune query 1416166 to fetch Safe families on Ethereum mainnet
    pub async fn fetch_child_safes(
        &self,
        parent: &str,
        index_from: i64,
        index_to: i64,
    ) -> Result<Vec<Address>> {
        // Query parameters for Safe Families query (query_id: 1416166)
        let params = vec![
            Parameter::text("Blockchain", "ethereum"),
            Parameter::text("ParentSafe", parent),
            Parameter::number("IndexFrom", &index_from.to_string()),
            Parameter::number("IndexTo", &index_to.to_string()),
        ];

        log::info!(
            "Fetching child safes from Dune for parent {} (indices {}-{})",
            parent,
            index_from,
            index_to
        );

        // Execute query and wait for results with 60 second timeout
        let results = self
            .client
            .refresh::<SafeFamilyRow>(1416166, Some(params), None)
            .await
            .map_err(|e| anyhow::anyhow!("Failed to execute and fetch Dune query: {:?}", e))?;

        let rows = results.result.rows;

        if rows.is_empty() {
            anyhow::bail!("No results returned for parent {}", parent);
        }

        log::info!("Got fleet of size {}", rows.len());

        // Parse addresses
        let addresses: Result<Vec<Address>> = rows
            .iter()
            .map(|row| {
                Address::from_str(&row.bracket)
                    .with_context(|| format!("Invalid address: {}", row.bracket))
            })
            .collect();

        addresses
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_dune_client_creation() {
        let api_key = std::env::var("DUNE_API_KEY");
        if api_key.is_err() {
            eprintln!("DUNE_API_KEY is not set - skipping test");
            return;
        }
        let client = DuneClient::new(api_key.unwrap());
        let safes = client
            .fetch_child_safes("0x20026f06342e16415b070ae3bdb3983af7c51c95", 0, 10)
            .await
            .unwrap();
        eprintln!("safes: {:#?}", safes);
        assert!(!safes.is_empty());
    }
}
