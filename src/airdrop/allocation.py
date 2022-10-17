"""Airdrop Allocation Data fetched from Safe Foundation hosted API service."""
from __future__ import annotations

import json
from dataclasses import dataclass

import requests
from web3 import Web3

from src.abis.load import load_contract_abi
from src.environment import CLIENT

AIRDROP_CONTRACT = CLIENT.w3.eth.contract(
    address=Web3().toChecksumAddress("0xA0b937D5c8E32a80E3a8ed4227CD020221544ee6"),
    abi=load_contract_abi("airdrop"),
)

ALLOCATION_BASE_URL = "https://safe-claiming-app-data.gnosis-safe.io/allocations"
MAX_U128 = 340282366920938463463374607431768211455

# redeem(
#     curveType(uint8)
#     durationWeeks(uint16)
#     startDate(uint64)
#     amount(uint128)
#     proof(bytes32[])
# )
RedeemParams = tuple[int, int, int, int, list[str]]
# claimVestedTokens[ViaModule](
#     vestingId(bytes32)
#     beneficiary(address)
#     tokensToClaim(uint128) = MAX_U128
# )
ClaimParams = tuple[str, str, int]


@dataclass
class Allocation:
    """
    Represents Safe Airdrop Allocation Data
    using primitive python types to make parsing easier
    Assuming the incoming data is correct (since it is coming from Safe Foundation)
    """

    # pylint:disable=invalid-name,too-many-instance-attributes
    tag: str
    account: str
    chainId: int
    contract: str
    vestingId: str
    durationWeeks: int
    startDate: int
    amount: str
    curve: int  # Could be an Enum
    proof: list[str]

    @staticmethod
    def api_url(address: str) -> str:
        """Returns dynamically constructed API URL"""
        chain_id = 1  # Airdrop was only on mainnet (so far...)
        return f"{ALLOCATION_BASE_URL}/{chain_id}/{address}.json"

    @classmethod
    def from_address(cls, safe_address: str) -> Allocation:
        """
        Fetches and Parses Response for Safe Allocation Data
        Note that Safes received multiple Allocations (of different types)
        so this constructor returns a list.
        """
        response = requests.get(url=cls.api_url(safe_address), timeout=5)
        if not response.ok:
            if "NoSuchKey" in response.text:
                raise FileNotFoundError(
                    f"{safe_address} is not eligible for SAFE airdrop"
                )

            raise RuntimeError(
                f"Allocation Request failed with unhandled response {response.text}"
            )

        allocations: list[Allocation] = [
            json.loads(json.dumps(entry), object_hook=lambda d: Allocation(**d))
            for entry in response.json()
        ]
        if len(allocations) > 1:
            # TODO - implement nested redemption
            print(
                f"Detected {len(allocations)} allocations for {safe_address} - taking the first!"
            )
        # First entry should be "user" allocation
        return allocations[0]

    def as_redeem_params(self) -> RedeemParams:
        """
        curveType(uint8)
        durationWeeks(uint16)
        startDate(uint64)
        amount(uint128)
        proof(bytes32[]):
        """
        return (
            self.curve,
            self.durationWeeks,
            self.startDate,
            # received and stored as a string, but is solidity uint128.
            int(self.amount),
            self.proof,
        )

    def as_claim_params(self, beneficiary: str) -> ClaimParams:
        """
        vestingId(bytes32):
        beneficiary(address):
        tokensToClaim(uint128) = MAX_U128
        """
        return self.vestingId, beneficiary, MAX_U128
