"""Stand alone script argument parsing logic"""
from __future__ import annotations
import argparse
from dataclasses import dataclass

from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe
from web3 import Web3

from src.safe import get_safe


@dataclass
class SafeFamily:
    """
    Simple data class holding a Safe and a collection of Sub Safes
    """
    parent: ChecksumAddress
    children: list[ChecksumAddress]

    @classmethod
    def from_args(cls) -> SafeFamily:
        """Parses Instance of class from command line arguments."""
        parser = argparse.ArgumentParser("Safe Family Arguments")
        parser.add_argument(
            "--parent",
            type=str,
            required=True,
            help="Master Safe Address (owner of all sub safes)",
        )
        parser.add_argument(
            "--sub-safes",
            type=str,
            required=True,
            help="List of Ethereum addresses corresponding to Safes owned by parent safe",
        )
        args = parser.parse_args()
        return cls(
            parent=Web3().toChecksumAddress(args.parent),
            children=[Web3().toChecksumAddress(c) for c in args.sub_safes.split(",")],
        )

    def as_safes(self, eth_client: EthereumClient) -> tuple[Safe, list[Safe]]:
        """Constructs/Fetches and returns Safe Objects from the instance attributes"""
        parent = get_safe(self.parent, eth_client)
        children = []
        for child in self.children:
            child_safe = get_safe(child, eth_client)
            if not child_safe.retrieve_is_owner(parent.address):
                print(
                    f"{parent} is not an owner of {child_safe} - transactions to fail!"
                )
            children.append(child_safe)

        print(f"loaded Parent {parent.address} along with {len(children)} child safes")
        return parent, children
