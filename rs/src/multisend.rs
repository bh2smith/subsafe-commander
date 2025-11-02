use alloy::dyn_abi::DynSolValue;
use alloy::primitives::{Address, Bytes, U256, keccak256};
use anyhow::Result;

use crate::safe::tx::SafeOperation;
use crate::utils::partition_array;

/// Multisend contract address
pub const MULTISEND_CONTRACT: &str = "0x9641d764fc13c8B624c04430C7356C1C7C8102e2";

/// Maximum number of transactions per batch
/// See benchmarks: https://github.com/bh2smith/subsafe-commander/issues/4#issuecomment-1297738947
pub const BATCH_SIZE_LIMIT: usize = 80;

/// A transaction for multisend
#[derive(Debug, Clone)]
pub struct MultiSendTx {
    pub operation: SafeOperation,
    pub to: Address,
    pub value: U256,
    pub data: Bytes,
}

impl MultiSendTx {
    /// Create a new multisend transaction with CALL operation
    pub fn new(to: Address, value: U256, data: Bytes) -> Self {
        Self {
            operation: SafeOperation::Call,
            to,
            value,
            data,
        }
    }

    /// Encode this transaction for multisend
    pub fn encode(&self) -> Vec<u8> {
        let mut encoded = Vec::new();

        // Operation (1 byte)
        encoded.push(self.operation as u8);

        // To address (20 bytes)
        encoded.extend_from_slice(self.to.as_slice());

        // Value (32 bytes)
        let value_bytes = self.value.to_be_bytes::<32>();
        encoded.extend_from_slice(&value_bytes);

        // Data length (32 bytes)
        let data_len = self.data.len();
        let len_bytes = U256::from(data_len).to_be_bytes::<32>();
        encoded.extend_from_slice(&len_bytes);

        // Data
        encoded.extend_from_slice(&self.data);

        encoded
    }
}

/// Build encoded multisend data from a list of transactions
pub fn build_encoded_multisend(transactions: &[MultiSendTx]) -> Result<Bytes> {
    log::info!("Packing {} transactions into MultiSend", transactions.len());

    if transactions.len() > BATCH_SIZE_LIMIT {
        anyhow::bail!(
            "Too many transactions for single batch ({}), use partitioned build!",
            transactions.len()
        );
    }

    // Concatenate all encoded transactions
    let mut encoded_txs = Vec::new();
    for tx in transactions {
        encoded_txs.extend_from_slice(&tx.encode());
    }
    // Call the contract with the selector + ABI-encoded bytes only once:
    let selector = &keccak256("multiSend(bytes)")[..4];
    let call_data = [selector, &DynSolValue::Bytes(encoded_txs).abi_encode()].concat();

    Ok(Bytes::from(call_data))
}

/// Partition transactions into batches according to BATCH_SIZE_LIMIT
pub fn partition_transactions(transactions: &[MultiSendTx]) -> Result<Vec<Vec<MultiSendTx>>> {
    let partitions = partition_array(transactions, BATCH_SIZE_LIMIT)?;

    if partitions.len() == 1 {
        log::info!("Building a single multi-exec transaction");
    } else {
        log::info!(
            "Partitioned {} transactions into {} batches",
            transactions.len(),
            partitions.len()
        );
    }

    Ok(partitions)
}

#[cfg(test)]
mod tests {
    use std::str::FromStr;

    use crate::ops::airdrop::transactions_for;

    use super::*;

    #[test]
    fn test_multisend_tx_encode() {
        let tx = MultiSendTx::new(
            Address::ZERO,
            U256::from(100),
            Bytes::from(vec![0x01, 0x02, 0x03]),
        );

        let encoded = tx.encode();

        // Check operation byte
        assert_eq!(encoded[0], 0);

        // Check that encoding has the right length
        // 1 (op) + 20 (address) + 32 (value) + 32 (data len) + 3 (data)
        assert_eq!(encoded.len(), 88);
    }

    #[test]
    fn test_partition_transactions() {
        let txs: Vec<MultiSendTx> = (0..200)
            .map(|i| MultiSendTx::new(Address::ZERO, U256::from(i), Bytes::from(vec![])))
            .collect();

        let partitions = partition_transactions(&txs).unwrap();

        // Should be partitioned into 3 batches: 80, 80, 40
        assert_eq!(partitions.len(), 3);
        assert_eq!(partitions[0].len(), 80);
        assert_eq!(partitions[1].len(), 80);
        assert_eq!(partitions[2].len(), 40);
    }

    #[tokio::test]
    async fn test_build_encoded_multisend() {
        let parent = Address::from_str("0x20026F06342e16415b070ae3bdB3983AF7c51C95").unwrap();
        let children =
            ["0x8926c4d7f8ada5b74827bfea51ae60517dde21cf"].map(|x| Address::from_str(x).unwrap());
        let txs = transactions_for(parent, children.as_slice()).await.unwrap();
        let x = build_encoded_multisend(&txs).unwrap();
        // Updated to match correct behavior: MultiSendTx targets child safe, not airdrop contract
        assert_eq!(
            hex::encode(x),
            "8d80ff0a00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000572008926c4d7f8ada5b74827bfea51ae60517dde21cf000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002646a761202000000000000000000000000a0b937d5c8e32a80e3a8ed4227cd020221544ee60000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001e00000000000000000000000000000000000000000000000000000000000000064166bbd3b42d030c88d965b91acbcdbe5243c86ff2720c4a68551fdd8ff1c4b732048dd1a00000000000000000000000020026f06342e16415b070ae3bdb3983af7c51c9500000000000000000000000000000000ffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004100000000000000000000000020026f06342e16415b070ae3bdb3983af7c51c9500000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000008926c4d7f8ada5b74827bfea51ae60517dde21cf000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002646a761202000000000000000000000000c0fde70a65c7569fe919be57492228dee8cdb5850000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001e00000000000000000000000000000000000000000000000000000000000000064166bbd3b94c5a4c996651070ac0e0c31fbffecc478ea48a1bee26aa395d4f608fdd38aa700000000000000000000000020026f06342e16415b070ae3bdb3983af7c51c9500000000000000000000000000000000ffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004100000000000000000000000020026f06342e16415b070ae3bdb3983af7c51c95000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        )
    }

    #[tokio::test]
    async fn test_build_encoded_multisend_empty() {
        let data = build_encoded_multisend(&[]).unwrap();
        // TODO Validate the encoded multisend.
        assert_eq!(
            hex::encode(data),
            "8d80ff0a00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"
        )
    }
}
