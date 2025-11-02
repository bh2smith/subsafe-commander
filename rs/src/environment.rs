use alloy::network::Ethereum;
use alloy::primitives::Address;
use alloy::providers::{Provider, RootProvider};
use alloy::rpc::client::RpcClient;
use alloy::signers::local::PrivateKeySigner;
use anyhow::{Context, Result};
use dotenvy::dotenv;
use std::env;
use std::str::FromStr;
use std::sync::Arc;

/// Configuration loaded from environment variables
#[derive(Debug, Clone)]
pub struct Config {
    // TODO: Direct exec for single owner safe (i.e. when proposer is owner).
    pub _provider: Arc<RootProvider<Ethereum>>,
    pub proposer: Option<PrivateKeySigner>,
    pub dune_api_key: Option<String>,
    pub _parent_safe: Option<Address>,
}

impl Config {
    /// Load configuration from environment variables
    pub async fn from_env() -> Result<Self> {
        // Load .env file if it exists
        let _ = dotenv();

        let node_url =
            env::var("NODE_URL").unwrap_or_else(|_| "http://reth.dappnode:8545".to_string());

        let dune_api_key = env::var("DUNE_API_KEY").ok();
        let proposer = if let Ok(proposer_pk) = env::var("PROPOSER_PK") {
            Some(PrivateKeySigner::from_str(&proposer_pk)?)
        } else {
            None
        };
        let provider = RootProvider::new(RpcClient::new_http(node_url.parse()?));

        // Log the network we're connected to
        let chain_id = provider
            .get_chain_id()
            .await
            .context("Failed to get chain ID")?;
        log::info!("Using network with chain ID: {}", chain_id);

        Ok(Self {
            _provider: Arc::new(provider),
            proposer,
            _parent_safe: env::var("PARENT_SAFE")
                .ok()
                .as_ref()
                .map(|x| Address::from_str(x))
                .transpose()?,
            dune_api_key,
        })
    }
}
