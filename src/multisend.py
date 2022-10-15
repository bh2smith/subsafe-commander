"""
All the tools necessary to compose and encode a
Safe Multisend transaction consisting of Transfers
"""
import logging.config

import safe_cli
from gnosis.eth.ethereum_client import EthereumClient
from gnosis.safe import Safe
from gnosis.safe.multi_send import MultiSend, MultiSendOperation, MultiSendTx

# This dependency can be removed once this issue is resolved:
# https://github.com/safe-global/safe-eth-py/issues/284
from safe_cli.api.transaction_service_api import TransactionServiceApi

log = logging.getLogger(__name__)

MULTISEND_CONTRACT = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"


def build_encoded_multisend(
    transactions: list[MultiSendTx], client: EthereumClient
) -> bytes:
    """ "Encodes a list of transfers into Multi Send Transaction"""
    multisend = MultiSend(ethereum_client=client)
    print(f"packing {len(transactions)} transfers into MultiSend")
    return multisend.build_tx_data(transactions)


def post_multisend(
    safe: Safe,
    transactions: list[MultiSendTx],
    client: EthereumClient,
    signing_key: str,
) -> int:
    """
    Posts a MultiSend Transaction from a list of Transfers.
    On success: Returns an integer representing resulting parent safe transaction nonce
    On Safe Transaction Service Error: Returns -1
    """
    encoded_multisend = build_encoded_multisend(
        transactions=transactions, client=client
    )
    assert isinstance(MultiSendOperation.DELEGATE_CALL.value, int)
    safe_tx = safe.build_multisig_tx(
        to=MULTISEND_CONTRACT,
        value=0,
        data=encoded_multisend,
        operation=MultiSendOperation.DELEGATE_CALL.value,
    )
    # There is a deep warning being raised here:
    # Details in issue: https://github.com/safe-global/safe-eth-py/issues/294
    safe_tx.sign(signing_key)
    tx_service = TransactionServiceApi(client, client.get_network())
    print(
        f"posting transaction with hash"
        f" {safe_tx.safe_tx_hash.hex()} to {safe.address}"
    )
    # TODO - command prompt are you sure
    try:
        tx_service.post_transaction(safe_address=safe.address, safe_tx=safe_tx)
        return int(safe_tx.safe_nonce)
    except safe_cli.api.transaction_service_api.BaseAPIException as err:
        print(
            f"Transaction NOT posted failing gracefully with "
            f"Safe Transaction service Base API error:"
            f"{err} and returning -1 (an invalid safe transaction nonce)"
        )
        return -1
