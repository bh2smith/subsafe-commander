use alloy::dyn_abi::DynSolValue;
use alloy::primitives::{Bytes, U256};
use anyhow::Result;

use crate::ops::airdrop::allocation::Allocation;
use crate::safe::tx::SafeTransaction;

/// Encode a claim transaction for the Safe airdrop
pub fn encode_claim(allocation: &Allocation, beneficiary: &str) -> Result<SafeTransaction> {
    let contract_address = allocation.contract_address()?;

    // claimVestedTokens(bytes32 vestingId, address beneficiary, uint128 tokensToClaim)
    let method_signature = "claimVestedTokens(bytes32,address,uint128)";
    let selector = &alloy::primitives::keccak256(method_signature.as_bytes())[..4];

    let params = allocation.encoded_claim_params(beneficiary)?;

    let mut data = Vec::from(selector);
    let tuple = DynSolValue::Tuple(params);
    let encoded_params = tuple.abi_encode_params();
    data.extend_from_slice(&encoded_params);

    Ok(SafeTransaction::new(
        contract_address,
        U256::ZERO,
        Bytes::from(data),
    ))
}

#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn test_encode_claim() {
        let allocation = Allocation {
            tag: "user".to_string(),
            account: "0x8926c4D7F8AdA5B74827bFEa51aE60517Dde21cf".to_string(),
            chain_id: 1,
            contract: "0xA0b937D5c8E32a80E3a8ed4227CD020221544ee6".to_string(),
            vesting_id: "0x42d030c88d965b91acbcdbe5243c86ff2720c4a68551fdd8ff1c4b732048dd1a"
                .to_string(),
            duration_weeks: 52,
            start_date: 1234567890,
            amount: "617828971259105640448".to_string(),
            curve: 0,
            proof: vec![],
        };

        let beneficiary = "0x20026F06342e16415b070ae3bdB3983AF7c51C95";
        let tx = encode_claim(&allocation, beneficiary).unwrap();

        assert_eq!(tx.to, allocation.contract_address().unwrap());
        assert_eq!(
            hex::encode(tx.data),
            "166bbd3b42d030c88d965b91acbcdbe5243c86ff2720c4a68551fdd8ff1c4b732048dd1a00000000000000000000000020026f06342e16415b070ae3bdb3983af7c51c9500000000000000000000000000000000ffffffffffffffffffffffffffffffff"
        );
    }
}
