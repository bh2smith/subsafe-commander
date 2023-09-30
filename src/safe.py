"""Some Safe object Helpers"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional, Any

from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.multi_send import MultiSendTx
from web3 import Web3
from web3.contract import Contract  # type:ignore

from src.constants import ZERO_ADDRESS
from src.dune import fetch_child_safes
from src.log import set_log
from src.multisend import (
    post_safe_tx,
    partitioned_build_multisend,
)

log = set_log(__name__)


def get_safe(address: str, client: EthereumClient) -> Safe:
    """
    Fetches safe object at address
    Safe must exist on the `client.get_network()`
    """
    return Safe(address=Web3.to_checksum_address(address), ethereum_client=client)


@dataclass
class SafeTransaction:
    """Basic Safe Transaction Data"""

    to: ChecksumAddress  # pylint:disable=invalid-name
    value: int
    data: HexStr
    operation: SafeOperation


def encode_contract_method(
    contract: Contract, method: str, params: list[Any], value: int = 0
) -> SafeTransaction:
    """
    Encodes the Contract.method{value}(params) as a SafeTransaction
    """
    log.info(f"Building {method}({params}) with value {value / 10**18:.6f} ETH")
    return SafeTransaction(
        to=contract.address,
        value=value,
        data=contract.encodeABI(method, params),
        operation=SafeOperation.CALL,
    )


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
            default=1000,
            help="Index in (sorted) list of children to perform operation to",
        )

        args, _ = parser.parse_known_args()
        parent = Web3().to_checksum_address(args.parent)
        if args.sub_safes is not None:
            children = [
                Web3().to_checksum_address(c) for c in args.sub_safes.split(",")
            ]
        else:
            start = args.index_from
            length = args.num_safes
            children = fetch_child_safes(parent, start, start + length)

        print(f"Using {len(children)} child safes {children}")
        return cls(parent, children)

    def as_safes(self, eth_client: EthereumClient) -> tuple[Safe, list[Safe]]:
        """Constructs/Fetches and returns Safe Objects from the instance attributes"""
        print(f"loading {len(self.children) + 1} Safe instances...")
        parent = get_safe(self.parent, eth_client)
        children = []
        # TODO - make this async!
        for child in self.children:
            child_safe = get_safe(child, eth_client)
            if not child_safe.retrieve_is_owner(parent.address):
                print(f"{parent} not an owner of {child_safe}: transactions will fail!")
            children.append(child_safe)

        print(f"loaded parent {parent.address} along with {len(children)} child Safes")
        return parent, children


def multi_exec(
    parent: Safe,
    client: EthereumClient,
    signing_key: str,
    transactions: list[MultiSendTx],
) -> list[int]:
    """
    Iteratively builds and posts a multisend transaction adding `new_owner` to each child safe.
    Requires that `parent` is a single signer on all `children`.
    """
    tx_service = TransactionServiceApi(client.get_network())
    return [
        post_safe_tx(safe_tx=tx, tx_service=tx_service)
        for tx in partitioned_build_multisend(
            safe=parent,
            transactions=transactions,
            client=client,
            signing_key=signing_key,
        )
    ]
