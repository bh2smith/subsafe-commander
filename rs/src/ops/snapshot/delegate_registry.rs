use alloy::primitives::Address;
use std::str::FromStr;

/// Snapshot delegation contract address
pub const DELEGATION_CONTRACT: &str = "0x469788fE6E9E9681C6ebF3bF78e7Fd26Fc015446";

/// Holds logic for constructing and converting various representations of a Delegation ID
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DelegationId {
    bytes: [u8; 32],
}

impl DelegationId {
    /// Build from a regular string, padding with zeros
    pub fn from_str(value_str: &str) -> Self {
        let mut bytes = [0u8; 32];
        let value_bytes = value_str.as_bytes();
        let len = std::cmp::min(value_bytes.len(), 32);
        bytes[..len].copy_from_slice(&value_bytes[..len]);
        Self { bytes }
    }

    /// Get hex representation
    pub fn hex(&self) -> String {
        format!("0x{}", hex::encode(self.bytes))
    }

    /// Get bytes representation
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.bytes
    }
}

impl std::fmt::Display for DelegationId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.hex())
    }
}

/// Lazy static for SAFE_DELEGATION_ID
pub const SAFE_DELEGATION_ID: &str = "safe.eth";

/// Get the delegation contract address
pub fn delegation_address() -> Address {
    Address::from_str(DELEGATION_CONTRACT).expect("Invalid delegation contract address")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_delegation_id_hex() {
        let id = DelegationId::from_str("safe.eth");
        let hex = id.hex();
        assert!(hex.starts_with("0x"));
        assert_eq!(hex.len(), 66); // 0x + 64 hex chars
    }

    #[test]
    fn test_delegation_id_equality() {
        let id1 = DelegationId::from_str("safe.eth");
        let id2 = DelegationId::from_str("safe.eth");
        assert_eq!(id1, id2);
    }

    #[test]
    fn test_delegation_address() {
        let addr = delegation_address();
        assert_eq!(
            format!("{:?}", addr),
            "0x469788fe6e9e9681c6ebf3bf78e7fd26fc015446"
        );
    }
}
