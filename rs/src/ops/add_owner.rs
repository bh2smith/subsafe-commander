use alloy::dyn_abi::DynSolValue;
use alloy::primitives::{Address, Bytes, U256};
use anyhow::Result;

use crate::multisend::MultiSendTx;
use crate::safe::tx::SafeTransaction;

/// Arguments for adding an owner to a Safe
#[derive(Debug, Clone)]
pub struct AddOwnerArgs {
    pub new_owner: Address,
    pub threshold: u64,
}

impl AddOwnerArgs {
    /// Create new AddOwnerArgs with custom threshold
    pub fn with_threshold(new_owner: Address, threshold: u64) -> Self {
        Self {
            new_owner,
            threshold,
        }
    }
}

/// Build a multisend transaction for adding an owner with threshold
pub fn build_add_owner_with_threshold(
    parent_address: Address,
    sub_safe_address: Address,
    params: &AddOwnerArgs,
) -> Result<MultiSendTx> {
    log::info!(
        "Building addOwnerWithThreshold({:?}, {}) on {:?} as MultiSendTx from {:?}",
        params.new_owner,
        params.threshold,
        sub_safe_address,
        parent_address
    );

    // Encode addOwnerWithThreshold(address owner, uint256 _threshold)
    let method_signature = "addOwnerWithThreshold(address,uint256)";
    let selector = &alloy::primitives::keccak256(method_signature.as_bytes())[..4];

    let method_params = vec![
        DynSolValue::Address(params.new_owner),
        DynSolValue::Uint(U256::from(params.threshold), 256),
    ];

    let mut data = Vec::from(selector);
    let tuple = DynSolValue::Tuple(method_params);
    let encoded_params = tuple.abi_encode_params();
    data.extend_from_slice(&encoded_params);

    let transaction = SafeTransaction::new(sub_safe_address, U256::ZERO, Bytes::from(data));

    transaction.as_multisend(sub_safe_address, &parent_address)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[test]
    fn test_add_owner_args_with_threshold() {
        let owner = Address::from_str("0x1234567890123456789012345678901234567890").unwrap();
        let args = AddOwnerArgs::with_threshold(owner, 2);

        assert_eq!(args.new_owner, owner);
        assert_eq!(args.threshold, 2);
    }

    #[test]
    fn test_build_add_owner_with_threshold() {
        let parent = Address::from_str("0x1234567890123456789012345678901234567890").unwrap();
        let child = Address::from_str("0xabcdefabcdefabcdefabcdefabcdefabcdefabcd").unwrap();
        let new_owner = Address::from_str("0x9876543210987654321098765432109876543210").unwrap();

        let args = AddOwnerArgs::with_threshold(new_owner, 1);
        let tx = build_add_owner_with_threshold(parent, child, &args).unwrap();

        assert_eq!(tx.to, child);
        assert_eq!(tx.value, U256::ZERO);
        assert!(!tx.data.is_empty());
    }
}
