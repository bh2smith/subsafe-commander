"""Snapshot delegation contract, type and method encodings"""
from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3

from src.abis.load import load_contract_abi
from src.environment import CLIENT

DELEGATION_CONTRACT = CLIENT.w3.eth.contract(
    address=Web3().toChecksumAddress("0x469788fE6E9E9681C6ebF3bF78e7Fd26Fc015446"),
    abi=load_contract_abi("delegate_registry"),
)


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
    def hex(self) -> HexDelegationId:
        """Returns hex representation"""
        return "0x" + self.bytes.hex()

    def __str__(self) -> str:
        """Returns string representation"""
        return self.bytes.decode("utf-8").replace("\x00", "")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DelegationId):
            return False
        return self.bytes == other.bytes


HexDelegationId = str  # Hex Representation of Bytes32
# Read
# delegation(delegator(address), id(bytes32))
DelegationParams = tuple[str, HexDelegationId]
# Write:
# clearDelegate(id(bytes32[]))
ClearDelegateParams = tuple[HexDelegationId]
# clearDelegate(id(bytes32[]), delegate(address))
SetDelegateParams = tuple[DelegationId, HexDelegationId]
