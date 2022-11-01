"""
All the tools necessary to compose and encode a
Safe Multisend transaction consisting of Transfers
"""
import logging.config
import sys
from typing import Optional

from eth_typing.encoding import HexStr
from gnosis.eth.ethereum_client import EthereumClient
from gnosis.safe import Safe, SafeTx, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.api.base_api import SafeAPIException
from gnosis.safe.multi_send import MultiSend, MultiSendTx, MultiSendOperation

from src.util import partition_array

log = logging.getLogger(__name__)

MULTISEND_CONTRACT = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"
# See benchmarks:
# https://github.com/bh2smith/subsafe-commander/issues/4#issuecomment-1297738947
BATCH_SIZE_LIMIT = 80


def build_encoded_multisend(
    transactions: list[MultiSendTx], client: EthereumClient
) -> bytes:
    """ "Encodes a list of transfers into Multi Send Transaction"""
    print(f"packing {len(transactions)} transactions into MultiSend")
    return MultiSend(ethereum_client=client).build_tx_data(transactions)


def post_safe_tx(safe_tx: SafeTx, tx_service: TransactionServiceApi) -> int:
    """
    Posts a Signed Safe Transaction.
    On success: Returns an integer representing resulting parent safe transaction nonce
    On Safe Transaction Service Error: Returns -1
    """
    assert safe_tx.signatures != b"", "Attempt to post unsigned transaction!"
    address, tx_hash = safe_tx.safe_address, safe_tx.safe_tx_hash.hex()
    print(f"posting transaction with hash {tx_hash} to {address}")
    if input("are you sure? (y/n) ") != "y":
        sys.exit()
    try:
        tx_service.post_transaction(safe_tx)
        return int(safe_tx.safe_nonce)
    except SafeAPIException as err:
        print(
            f"Transaction NOT posted failing gracefully with "
            f"Safe Transaction service Base API error:"
            f"{err} and returning -1 (an invalid safe transaction nonce)"
        )
        return -1


def build_and_sign_multisend(
    safe: Safe,
    transactions: list[MultiSendTx],
    client: EthereumClient,
    signing_key: str,
    nonce: Optional[int] = None,
) -> SafeTx:
    """
    Constructs and Signs a MultiSend Transaction from a list of Transfers.
    """
    if len(transactions) <= BATCH_SIZE_LIMIT:
        raise RuntimeError(
            "too many transactions for single batch ({len(transactions)}), "
            "use partitioned_build_multisend!"
        )
    encoded_multisend = build_encoded_multisend(
        transactions=transactions, client=client
    )
    # This is a weird type issue.
    assert isinstance(SafeOperation.DELEGATE_CALL.value, int)
    safe_tx = safe.build_multisig_tx(
        to=MULTISEND_CONTRACT,
        value=0,
        data=encoded_multisend,
        operation=SafeOperation.DELEGATE_CALL.value,
        safe_nonce=nonce,
    )
    # There is a deep warning being raised here:
    # Details in issue: https://github.com/safe-global/safe-eth-py/issues/294
    safe_tx.sign(signing_key)
    return safe_tx


def partitioned_build_multisend(
    safe: Safe,
    transactions: list[MultiSendTx],
    client: EthereumClient,
    signing_key: str,
) -> list[SafeTx]:
    """
    Partitions transactions according to what will fit in BATCH_SIZE_LIMIT
    and builds as many transactions as necessary with appropriate nonce
    beginning from the current nonce of `safe`.
    """
    partition = partition_array(transactions, BATCH_SIZE_LIMIT)
    if len(partition) == 1:
        log.info("building an executing a single multi-exec transaction")
    else:
        log.info(f"partitioned {len(transactions)} into {len(partition)} batches")
    nonce = safe.retrieve_nonce()
    return [
        build_and_sign_multisend(safe, part, client, signing_key, nonce + i)
        for i, part in enumerate(partition)
    ]


def build_multisend_from_data(safe: Safe, data: HexStr, value: int = 0) -> MultiSendTx:
    """Constructs a MultiSend Transaction for Safe with provided Data"""
    return MultiSendTx(
        to=safe.address,
        value=value,
        data=data,
        operation=MultiSendOperation.CALL,
    )
