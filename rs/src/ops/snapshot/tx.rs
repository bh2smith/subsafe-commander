use alloy::dyn_abi::DynSolValue;
use alloy::primitives::{Address, U256};
use anyhow::Result;

use crate::multisend::MultiSendTx;
use crate::ops::snapshot::delegate_registry::{
    DelegationId, SAFE_DELEGATION_ID, delegation_address,
};
use crate::safe::tx::encode_contract_method;

/// Snapshot contract commands
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SnapshotCommand {
    SetDelegate,
    ClearDelegate,
}

impl SnapshotCommand {
    /// Get the method name for this command
    pub fn method_name(&self) -> &str {
        match self {
            SnapshotCommand::SetDelegate => "setDelegate",
            SnapshotCommand::ClearDelegate => "clearDelegate",
        }
    }
}

impl std::fmt::Display for SnapshotCommand {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.method_name())
    }
}

impl std::str::FromStr for SnapshotCommand {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> Result<Self> {
        match s {
            "setDelegate" => Ok(SnapshotCommand::SetDelegate),
            "clearDelegate" => Ok(SnapshotCommand::ClearDelegate),
            _ => anyhow::bail!("Invalid snapshot command: {}", s),
        }
    }
}

/// Build transactions for a given snapshot command
pub fn transactions_for(
    parent_address: Address,
    children: &[Address],
    command: SnapshotCommand,
    delegate: Option<Address>,
) -> Result<Vec<MultiSendTx>> {
    let delegation_contract = delegation_address();
    let delegation_id = DelegationId::from_str(SAFE_DELEGATION_ID);

    let (params, method_signature) = match command {
        SnapshotCommand::SetDelegate => {
            let delegate_addr = delegate.unwrap_or(parent_address);
            log::info!(
                "Setting delegation for namespace {} to {:?}",
                SAFE_DELEGATION_ID,
                delegate_addr
            );

            // setDelegate(bytes32 id, address delegate)
            let delegation_bytes = delegation_id.as_bytes();
            (
                vec![
                    DynSolValue::FixedBytes(delegation_bytes.into(), 32),
                    DynSolValue::Address(delegate_addr),
                ],
                "setDelegate(bytes32,address)",
            )
        }
        SnapshotCommand::ClearDelegate => {
            log::info!("Clearing delegation for namespace {}", SAFE_DELEGATION_ID);

            // clearDelegate(bytes32 id)
            let delegation_bytes = delegation_id.as_bytes();
            (
                vec![DynSolValue::FixedBytes(delegation_bytes.into(), 32)],
                "clearDelegate(bytes32)",
            )
        }
    };

    let mut transactions = Vec::new();

    for child in children {
        let safe_tx = encode_contract_method(
            delegation_contract,
            method_signature,
            params.clone(),
            U256::ZERO,
        );

        transactions.push(safe_tx.as_multisend(*child, &parent_address)?);
    }

    Ok(transactions)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[test]
    fn test_snapshot_command_from_str() {
        assert_eq!(
            "setDelegate".parse::<SnapshotCommand>().unwrap(),
            SnapshotCommand::SetDelegate
        );
        assert_eq!(
            "clearDelegate".parse::<SnapshotCommand>().unwrap(),
            SnapshotCommand::ClearDelegate
        );
    }

    #[test]
    fn test_snapshot_command_method_name() {
        assert_eq!(SnapshotCommand::SetDelegate.method_name(), "setDelegate");
        assert_eq!(
            SnapshotCommand::ClearDelegate.method_name(),
            "clearDelegate"
        );
    }

    #[test]
    fn test_transactions_for_empty() {
        let parent = Address::from_str("0x1234567890123456789012345678901234567890").unwrap();
        let children: Vec<Address> = vec![];

        let txs = transactions_for(parent, &children, SnapshotCommand::SetDelegate, None).unwrap();

        assert_eq!(txs.len(), 0);
    }
}
