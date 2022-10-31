"""Some Safe object Helpers"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.multi_send import MultiSendTx
from web3 import Web3

from src.constants import ZERO_ADDRESS
from src.dune import fetch_child_safes
from src.multisend import post_safe_tx, build_and_sign_multisend

# See benchmarks: 
# https://github.com/bh2smith/subsafe-commander/issues/4#issuecomment-1297738947
BATCH_SIZE_LIMIT = 80


def get_safe(address: str, client: EthereumClient) -> Safe:
    """
    Fetches safe object at address
    Safe must exist on the `client.get_network()`
    """
    return Safe(address=Web3.toChecksumAddress(address), ethereum_client=client)


@dataclass
class SafeTransaction:
    """Basic Safe Transaction Data"""

    to: ChecksumAddress  # pylint:disable=invalid-name
    value: int
    data: HexStr
    operation: SafeOperation


def encode_exec_transaction(
    safe: Safe, owner: ChecksumAddress, transaction: SafeTransaction
) -> HexStr:
    """
    Builds an ExecTransaction
    From the author's understanding, this is used for executing
    a transaction on behalf of a "SubSafe" from a parent (owner).
    This is why the signature looks the way it does.
    """
    sigs = (
        f"0x000000000000000000000000{owner.replace('0x', '')}00"
        f"0000000000000000000000000000000000000000000000000000000000000001"
    )
    data: HexStr = safe.contract.encodeABI(
        "execTransaction",
        [
            transaction.to,
            transaction.value,
            transaction.data,
            transaction.operation.value,
            0,
            0,
            0,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            sigs,
        ],
    )
    return data


@dataclass
class SafeFamily:
    """
    Simple data class holding a Safe and a collection of Sub Safes
    """

    parent: ChecksumAddress
    children: list[ChecksumAddress]

    @classmethod
    def from_args(cls, parser: Optional[argparse.ArgumentParser] = None) -> SafeFamily:
        """Parses Instance of class from command line arguments."""
        if parser is None:
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
            required=False,
            default=None,
            help="List of Ethereum addresses corresponding to Safes owned by parent safe",
        )
        parser.add_argument(
            "--index-from",
            type=int,
            default=0,
            help="Index in (sorted) list of children to perform operation from",
        )
        parser.add_argument(
            "--num-safes",
            type=int,
            default=BATCH_SIZE_LIMIT,
            help="Index in (sorted) list of children to perform operation to",
        )

        args, _ = parser.parse_known_args()
        parent = Web3().toChecksumAddress(args.parent)
        if args.sub_safes is not None:
            # TODO - assert BATCH SIZE LIMIT here too!
            children = [Web3().toChecksumAddress(c) for c in args.sub_safes.split(",")]
        else:
            start = args.index_from
            length = args.num_safes
            if length > BATCH_SIZE_LIMIT:
                print(
                    f"Sorry - transaction size may be too large {length} > {BATCH_SIZE_LIMIT}"
                )
                sys.exit()
            children = fetch_child_safes(parent, start, start + length)

        print(f"Using {len(children)} child safes {children}")
        return cls(parent, children)

    def as_safes(self, eth_client: EthereumClient) -> tuple[Safe, list[Safe]]:
        """Constructs/Fetches and returns Safe Objects from the instance attributes"""
        parent = get_safe(self.parent, eth_client)
        children = []
        for child in self.children:
            child_safe = get_safe(child, eth_client)
            if not child_safe.retrieve_is_owner(parent.address):
                print(f"{parent} not an owner of {child_safe}: transactions will fail!")
            children.append(child_safe)

        print(f"loaded Parent {parent.address} along with {len(children)} child safes")
        return parent, children


def multi_exec(
    parent: Safe,
    client: EthereumClient,
    signing_key: str,
    transactions: list[MultiSendTx],
) -> int:
    """
    Iteratively builds and posts a multisend transaction adding `new_owner` to each child safe.
    Requires that `parent` is a single signer on all `children`.
    """
    print("building an executing a multi-exec transaction")

    return post_safe_tx(
        safe_tx=build_and_sign_multisend(
            safe=parent,
            transactions=transactions,
            client=client,
            signing_key=signing_key,
        ),
        tx_service=TransactionServiceApi(client.get_network()),
    )
