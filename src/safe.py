"""Some Safe object Helpers"""
from dataclasses import dataclass

from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from web3 import Web3

from src.constants import ZERO_ADDRESS


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
