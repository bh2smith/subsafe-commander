"""Boilerplate code for encoding interactions with Airdrop Contract"""

from enum import Enum

from gnosis.safe import SafeOperation, Safe
from gnosis.safe.multi_send import MultiSendTx
from web3 import Web3

from src.airdrop.allocation import Allocation, AIRDROP_CONTRACT, MAX_U128
from src.multisend import build_multisend_from_data
from src.safe import SafeTransaction, encode_exec_transaction


def encode_redeem(allocation: Allocation) -> SafeTransaction:
    """
    Encodes the Safe Airdrop redeem transaction for a given Safe:
    The redeem function's arguments are fetched
    from an API service hosted by Safe Foundation
    """

    return SafeTransaction(
        to=Web3.to_checksum_address(allocation.contract),
        value=0,
        data=AIRDROP_CONTRACT.encodeABI("redeem", allocation.as_redeem_params()),
        operation=SafeOperation.CALL,
    )


def build_and_sign_redeem(
    safe: Safe, sub_safe: Safe, allocation: Allocation
) -> MultiSendTx:
    """
    :param safe: Safe owning each of this child safes
    :param sub_safe: Safe owned by Parent with signing threshold = 1
    :param allocation: contains function arguments for redeem tx
    :return: Multisend Transaction
    """
    return build_multisend_from_data(
        safe=sub_safe,
        data=encode_exec_transaction(
            sub_safe,
            safe.address,
            encode_redeem(allocation=allocation),
        ),
    )



def encode_claim(
    allocation: Allocation,
    beneficiary: str
) -> SafeTransaction:
    """
    Encodes the Safe Airdrop claimVestedViaModule transaction for a given Safe:
    """
    # Could also use allocation.as_claim_params(beneficiary) - not sure what is better.
    claim_params = [allocation.vestingId, beneficiary, MAX_U128]
    return SafeTransaction(
        to=Web3.to_checksum_address(allocation.contract),
        value=0,
        data=AIRDROP_CONTRACT.encodeABI("claimVestedTokens", claim_params),
        operation=SafeOperation.CALL,
    )


def build_and_sign_claim(
    safe: Safe, sub_safe: Safe, allocation: Allocation, beneficiary: str
) -> MultiSendTx:
    """
    :param safe: Safe owning each of this child safes
    :param sub_safe: Safe owned by Parent with signing threshold = 1
    :param allocation: contains function arguments for claim tx
    :param beneficiary: recipient address of token claim
    :return: Multisend Transaction
    """
    return build_multisend_from_data(
        safe=sub_safe,
        data=encode_exec_transaction(
            sub_safe,
            safe.address,
            encode_claim(
                allocation=allocation,
                beneficiary=beneficiary,
                method="claimVestedTokens",
            ),
        ),
    )
