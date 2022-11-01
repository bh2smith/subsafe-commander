"""Snapshot delegation contract, type and method encodings"""
from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3

from src.abis.load import load_contract_abi
from src.environment import CLIENT
from src.log import set_log

log = set_log(__name__)

DELEGATION_CONTRACT = CLIENT.w3.eth.contract(
    address=Web3().toChecksumAddress("0x469788fE6E9E9681C6ebF3bF78e7Fd26Fc015446"),
    abi=load_contract_abi("delegate_registry"),
)


# TODO - this should be a standard generic type converter (probably also works the same for ens).
@dataclass
class DelegationId:
    """Holds logic for constructing and converting various representations of a Delegation ID"""

    bytes: bytes

    @classmethod
    def from_str(cls, value_str: str) -> DelegationId:
        """Builds Object (bytes as base representation) from regular string."""
        return cls(bytes=value_str.encode("utf-8").ljust(32, b"\x00"))

    @classmethod
    def from_hex(cls, hex_value: str) -> DelegationId:
        """Builds Object (bytes as base representation) from hex string."""
        stripped_hex = hex_value.replace("0x", "")
        return cls(bytes=bytes.fromhex(stripped_hex))

    @property
    def hex(self) -> str:
        """Returns hex representation"""
        return "0x" + self.bytes.hex()

    def __str__(self) -> str:
        """Returns string representation"""
        return self.bytes.decode("utf-8").replace("\x00", "")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DelegationId):
            return False
        return self.bytes == other.bytes


SAFE_DELEGATION_ID = DelegationId.from_str("safe.eth")


## These methods below are unused currently `safe.encode_contract_method` used as generalization
# HexDelegationId = str  # Hex Representation of Bytes32
# # Read
# # delegation(delegator(address), id(bytes32))
# DelegationParams = tuple[str, HexDelegationId]
# # Write:
# # clearDelegate(id(bytes32[]))
# ClearDelegateParams = tuple[HexDelegationId]
# # setDelegate(id(bytes32[]), delegate(address))
# SetDelegateParams = tuple[DelegationId, HexDelegationId]
# def encode_set_delegate(
#     d_id: DelegationId, delegate: ChecksumAddress
# ) -> SafeTransaction:
#     """
#     Encodes the DelegateRegistry.setDelegate as a SafeTransaction
#     """
#     return encode_contract_method(
#         DELEGATION_CONTRACT, "setDelegate", [d_id.hex, delegate]
#     )
#
#
# def encode_clear_delegate(d_id: DelegationId) -> SafeTransaction:
#     """
#     Encodes the DelegateRegistry.clearDelegate as a SafeTransaction
#     """
#     return encode_contract_method(DELEGATION_CONTRACT, "clearDelegate", [d_id.hex])
