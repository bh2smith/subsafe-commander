"""
Everything required to Redeem a Safe Airdrop.
This, stand alone, script can also perform "multi redeem" on behalf of a family of safes
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests
from eth_typing.ethpm import URI
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from web3 import Web3

from src.args import SafeFamily
from src.environment import NODE_URL
from src.multisend import post_safe_tx, build_and_sign_multisend
from src.safe import SafeTransaction, encode_exec_transaction

CLIENT = EthereumClient(URI(NODE_URL))
with open("src/abis/airdrop.json", "r", encoding="utf-8") as f:
    AIRDROP_CONTRACT = CLIENT.w3.eth.contract(
        address=Web3().toChecksumAddress("0xA0b937D5c8E32a80E3a8ed4227CD020221544ee6"),
        abi=json.load(f),
    )

ALLOCATION_BASE_URL = "https://safe-claiming-app-data.gnosis-safe.io/allocations"

RedeemParams = tuple[int, int, int, int, list[str]]


@dataclass
class Allocation:
    """
    Represents Safe Airdrop Allocation Data
    using primitive python types to make parsing easier
    Assuming the incoming data is correct (since it is coming from Safe Foundation)
    """

    # pylint:disable=invalid-name
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
    def from_address(cls, safe_address: str) -> list[Allocation]:
        """
        Fetches and Parses Response for Safe Allocation Data
        Note that Safes received multiple Allocations (of different types)
        so this constructor returns a list.
        """
        response = requests.get(url=cls.api_url(safe_address), timeout=5)
        if not response.ok:
            raise RuntimeError(f"Allocation Request failed with response {response}")
        return [
            json.loads(json.dumps(entry), object_hook=lambda d: Allocation(**d))
            for entry in response.json()
        ]

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


def encode_redeem_tx(safe: Safe) -> SafeTransaction:
    """
    Encodes the Safe Airdrop redeem transaction for a given Safe:
    The redeem function's arguments are fetched
    from an API service hosted by Safe Foundation
    """
    allocations = Allocation.from_address(safe.address)
    if len(allocations) > 1:
        # TODO - implement nested redemption
        print(f"Detected {len(allocations)} allocations for {safe} - taking the first!")
    # First entry should be "user" allocation
    singular_allocation = allocations[0]

    return SafeTransaction(
        to=safe.address,
        value=0,
        data=AIRDROP_CONTRACT.encodeABI(
            "redeem", singular_allocation.as_redeem_params()
        ),
        operation=SafeOperation.CALL,
    )


def build_and_sign_redeem(safe: Safe, sub_safe: Safe) -> MultiSendTx:
    """
    :param safe: Safe owning each of this child safes
    :param sub_safe: Safe owned by Parent with signing threshold = 1
    :return: Multisend Transaction
    """
    assert sub_safe.retrieve_is_owner(
        safe.address
    ), f"{safe} not an owner of {sub_safe}"
    return MultiSendTx(
        to=sub_safe.address,
        value=0,
        data=encode_exec_transaction(
            sub_safe, safe.address, encode_redeem_tx(sub_safe)
        ),
        operation=MultiSendOperation.CALL,
    )


def multi_redeem(
    family: SafeFamily,
    client: EthereumClient,
    signing_key: str,
) -> int:
    """
    Iteratively builds and posts a multisend transaction adding `new_owner` to each child safe.
    Requires that `parent` is a single signer on all `children`.
    """
    parent, children = family.as_safes(client)
    print("building an executing a multi-redeem transaction")

    return post_safe_tx(
        safe_tx=build_and_sign_multisend(
            safe=parent,
            transactions=[
                build_and_sign_redeem(
                    safe=parent,
                    # Unfortunate thing about having this so deeply nested
                    # is that we can't log about the loaded child safes:
                    # functional programming ftw
                    sub_safe=child,
                )
                for child in children
            ],
            client=client,
            signing_key=signing_key,
        ),
        tx_service=TransactionServiceApi(client.get_network()),
    )


if __name__ == "__main__":
    multi_redeem(
        family=SafeFamily.from_args(),
        client=EthereumClient(URI(NODE_URL)),
        signing_key=os.environ["PROPOSER_PK"],
    )
