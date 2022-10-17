"""
Everything required to Redeem a Safe Airdrop.
This, stand alone, script can also perform "multi redeem" on behalf of a family of safes
"""
from __future__ import annotations

import os

from gnosis.safe import Safe, SafeOperation
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation

from src.airdrop.allocation import Allocation, AIRDROP_CONTRACT
from src.environment import CLIENT
from src.safe import SafeTransaction, encode_exec_transaction, multi_exec, SafeFamily


def encode_redeem(allocation: Allocation) -> SafeTransaction:
    """
    Encodes the Safe Airdrop redeem transaction for a given Safe:
    The redeem function's arguments are fetched
    from an API service hosted by Safe Foundation
    """

    return SafeTransaction(
        to=AIRDROP_CONTRACT.address,
        value=0,
        data=AIRDROP_CONTRACT.encodeABI("redeem", allocation.as_redeem_params()),
        operation=SafeOperation.CALL,
    )


# TODO - assert safe owns sub_safe
def build_and_sign_redeem(
    safe: Safe, sub_safe: Safe, allocation: Allocation
) -> MultiSendTx:
    """
    :param safe: Safe owning each of this child safes
    :param sub_safe: Safe owned by Parent with signing threshold = 1
    :param allocation: contains function arguments for redeem tx
    :return: Multisend Transaction
    """
    return MultiSendTx(
        to=sub_safe.address,
        value=0,
        data=encode_exec_transaction(
            sub_safe,
            safe.address,
            encode_redeem(allocation=allocation),
        ),
        operation=MultiSendOperation.CALL,
    )


if __name__ == "__main__":
    parent, children = SafeFamily.from_args().as_safes(CLIENT)
    nonce = multi_exec(
        parent,
        CLIENT,
        signing_key=os.environ["PROPOSER_PK"],
        transactions=[
            build_and_sign_redeem(
                safe=parent,
                sub_safe=child,
                allocation=Allocation.from_address(child.address),
            )
            for child in children
        ],
    )
