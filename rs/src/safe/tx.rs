use alloy::dyn_abi::DynSolValue;
use alloy::primitives::{Address, B256, Bytes, FixedBytes, U256, keccak256};
use alloy::providers::Provider;
use alloy::signers::SignerSync;
use alloy::signers::local::PrivateKeySigner;
use alloy::{hex, sol};
use anyhow::{Context, Result};

use crate::multisend::MultiSendTx;

/// Safe operation type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum SafeOperation {
    Call = 0,
    DelegateCall = 1,
}

/// Basic Safe Transaction Data
#[derive(Debug, Clone)]
pub struct SafeTransaction {
    pub to: Address,
    pub value: U256,
    pub data: Bytes,
    pub operation: SafeOperation,
    pub safe_tx_gas: U256,
    pub base_gas: U256,
    pub gas_price: U256,
    pub gas_token: Address,
    pub refund_receiver: Address,
    pub nonce: U256,
    pub signers: Vec<Address>,
    pub signatures: Vec<u8>, // concatenated 65-byte signatures
}

impl SafeTransaction {
    /// Create a new Safe transaction with CALL operation
    pub fn new(to: Address, value: U256, data: Bytes) -> Self {
        Self {
            to,
            value,
            data,
            operation: SafeOperation::Call,
            // We never use any of these.
            safe_tx_gas: U256::ZERO,
            base_gas: U256::ZERO,
            gas_price: U256::ZERO,
            gas_token: Address::ZERO,
            refund_receiver: Address::ZERO,
            nonce: U256::ZERO,
            signers: Vec::new(),
            signatures: Vec::new(),
        }
    }
    // Don't forget to set the nonce.
    pub fn with_nonce(mut self, nonce: U256) -> Self {
        self.nonce = nonce;
        self
    }

    pub fn with_operation(mut self, operation: SafeOperation) -> Self {
        self.operation = operation;
        self
    }

    pub fn hash(&self) -> B256 {
        // keccak256("SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
        let tx_typehash = keccak256(
        b"SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)"
    );

        let data_hash = keccak256(&self.data);

        // abi.encode(TYPEHASH, to, value, keccak256(data), operation, safeTxGas, baseGas, gasPrice, gasToken, refundReceiver, nonce)
        let encoded = DynSolValue::Tuple(vec![
            DynSolValue::FixedBytes(tx_typehash, 32),
            DynSolValue::Address(self.to),
            DynSolValue::Uint(self.value, 256),
            DynSolValue::FixedBytes(data_hash, 32),
            DynSolValue::Uint(U256::from(self.operation as u8), 8),
            DynSolValue::Uint(self.safe_tx_gas, 256),
            DynSolValue::Uint(self.base_gas, 256),
            DynSolValue::Uint(self.gas_price, 256),
            DynSolValue::Address(self.gas_token),
            DynSolValue::Address(self.refund_receiver),
            DynSolValue::Uint(self.nonce, 256),
        ])
        .abi_encode();

        keccak256(&encoded)
    }

    pub fn safe_tx_hash(&self, safe_address: Address, chain_id: U256) -> FixedBytes<32> {
        let domain = eip712_domain_separator(chain_id, safe_address);
        let tx_hash = self.hash();

        let mut preimage = Vec::with_capacity(2 + 32 + 32);
        preimage.extend_from_slice(b"\x19\x01");
        preimage.extend_from_slice(domain.as_slice());
        preimage.extend_from_slice(tx_hash.as_slice());

        keccak256(&preimage)
    }

    pub fn as_multisend(&self, safe_address: Address, owner: &Address) -> Result<MultiSendTx> {
        let exec_data = encode_exec_transaction(safe_address, owner, self)?;
        Ok(MultiSendTx::new(safe_address, U256::ZERO, exec_data))
    }

    pub fn sign(
        &mut self,
        safe_address: Address,
        chain_id: U256,
        signer: &PrivateKeySigner,
    ) -> Result<()> {
        let digest = self.safe_tx_hash(safe_address, chain_id);
        log::info!("Signing Safe transaction with hash: {:#?}", digest);
        let sig = signer.sign_hash_sync(&digest)?;
        let sig_bytes = sig.as_bytes().to_vec();
        let signer_addr = signer.address();

        // If already signed, skip
        if self.signers.contains(&signer_addr) {
            return Ok(());
        }

        // Determine sorted insert position
        let mut new_signers = self.signers.clone();
        new_signers.push(signer_addr);
        new_signers.sort();

        let pos = new_signers.iter().position(|a| *a == signer_addr).unwrap();

        // Insert signature bytes at correct offset (65 * index)
        let insert_at = pos * 65;
        self.signatures
            .splice(insert_at..insert_at, sig_bytes.clone());

        self.signers = new_signers;
        Ok(())
    }

    /// Retrieve concatenated signatures blob
    pub fn signatures_blob(&self) -> Bytes {
        Bytes::from(self.signatures.clone())
    }
}

/// Encode a contract method call
pub fn encode_contract_method(
    contract_address: Address,
    method_signature: &str,
    params: Vec<DynSolValue>,
    value: U256,
) -> SafeTransaction {
    // Create method selector (first 4 bytes of keccak256 hash)
    let selector = &keccak256(method_signature.as_bytes())[..4];

    log::info!(
        "Building {} with value {:.6} ETH",
        method_signature,
        value.to::<u128>() as f64 / 1e18
    );

    let mut data = Vec::from(selector);
    let tuple = DynSolValue::Tuple(params);
    data.extend_from_slice(&tuple.abi_encode_params());

    SafeTransaction::new(contract_address, value, Bytes::from(data))
}

/// Encode an execTransaction call for Safe
/// This is used for executing a transaction on behalf of a "SubSafe" from a parent (owner)
pub fn encode_exec_transaction(
    _safe_address: Address,
    owner: &Address,
    transaction: &SafeTransaction,
) -> Result<Bytes> {
    // Build the signature for a single owner approval
    // Format: 0x000000000000000000000000{owner}0000000000000000000000000000000000000000000000000000000000000001
    let owner_hex = hex::encode(owner.as_slice());
    let sigs = format!(
        "0x000000000000000000000000{}000000000000000000000000000000000000000000000000000000000000000001",
        owner_hex
    );

    let sig_bytes = hex::decode(&sigs[2..]).context("Failed to decode signature")?;

    // Build execTransaction call
    // function execTransaction(
    //     address to,
    //     uint256 value,
    //     bytes calldata data,
    //     Enum.Operation operation,
    //     uint256 safeTxGas,
    //     uint256 baseGas,
    //     uint256 gasPrice,
    //     address gasToken,
    //     address refundReceiver,
    //     bytes memory signatures
    // )
    let method_signature = "execTransaction(address,uint256,bytes,uint8,uint256,uint256,uint256,address,address,bytes)";
    let selector = &alloy::primitives::keccak256(method_signature.as_bytes())[..4];

    let params = vec![
        DynSolValue::Address(transaction.to),
        DynSolValue::Uint(transaction.value, 256),
        DynSolValue::Bytes(transaction.data.to_vec()),
        DynSolValue::Uint(U256::from(transaction.operation as u8), 8),
        DynSolValue::Uint(U256::ZERO, 256),  // safeTxGas
        DynSolValue::Uint(U256::ZERO, 256),  // baseGas
        DynSolValue::Uint(U256::ZERO, 256),  // gasPrice
        DynSolValue::Address(Address::ZERO), // gasToken
        DynSolValue::Address(Address::ZERO), // refundReceiver
        DynSolValue::Bytes(sig_bytes),       // signatures
    ];

    let mut data = Vec::from(selector);
    let tuple = DynSolValue::Tuple(params);
    data.extend_from_slice(&tuple.abi_encode_params());

    Ok(Bytes::from(data))
}

fn eip712_domain_separator(chain_id: U256, verifying_contract: Address) -> FixedBytes<32> {
    // keccak256("EIP712Domain(uint256 chainId,address verifyingContract)")
    let domain_typehash = keccak256(b"EIP712Domain(uint256 chainId,address verifyingContract)");

    // abi.encode(TYPEHASH, chainId, verifyingContract)
    let encoded = DynSolValue::Tuple(vec![
        DynSolValue::FixedBytes(domain_typehash, 32), // bytes32
        DynSolValue::Uint(chain_id, 256),             // uint256
        DynSolValue::Address(verifying_contract),     // address
    ])
    .abi_encode();

    keccak256(&encoded)
}

pub async fn get_safe_nonce(safe_address: Address, provider: &impl Provider) -> Result<U256> {
    sol! {
        #[sol(rpc)]
        interface ISafe {
            function nonce() external view returns (uint256);
        }
    }
    let safe = ISafe::new(safe_address, provider);
    let nonce = safe.nonce().call().await?;
    Ok(nonce)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_safe_operation() {
        assert_eq!(SafeOperation::Call as u8, 0);
        // assert_eq!(SafeOperation::DelegateCall as u8, 1);
    }

    #[test]
    fn test_safe_transaction_new() {
        let tx = SafeTransaction::new(
            Address::ZERO,
            U256::from(100),
            Bytes::from(vec![0x01, 0x02]),
        );

        assert_eq!(tx.to, Address::ZERO);
        assert_eq!(tx.value, U256::from(100));
        assert_eq!(tx.operation, SafeOperation::Call);
    }

    // #[test]
    // fn test_safe_family_from_addresses() {
    //     let parent = "0x1234567890123456789012345678901234567890";
    //     let children =
    //         "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd,0x9876543210987654321098765432109876543210";

    //     let family = SafeFamily::from_addresses(parent, Some(children)).unwrap();

    //     assert_eq!(family.children.len(), 2);
    // }

    #[test]
    fn test_encode_contract_method() {
        let contract = Address::ZERO;
        let tx = encode_contract_method(
            contract,
            "transfer(address,uint256)",
            vec![
                DynSolValue::Address(Address::ZERO),
                DynSolValue::Uint(U256::from(100), 256),
            ],
            U256::ZERO,
        );

        assert_eq!(tx.to, contract);
        assert_eq!(tx.operation, SafeOperation::Call);
        // Data should start with function selector
        assert!(tx.data.len() > 4);
    }
}
