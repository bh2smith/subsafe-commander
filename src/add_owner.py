"""A couple of helper methods associated with building ;nested Safe addOwnerWithThreshold method"""
from dataclasses import dataclass

from eth_typing.evm import ChecksumAddress
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from src.safe import SafeTransaction, encode_exec_transaction


@dataclass
class AddOwnerArgs:
    """Arguments passed into AddOwner method on a safe."""

    new_owner: ChecksumAddress
    threshold: int = 1

    def as_list(self) -> tuple[ChecksumAddress, int]:
        """Returns type passed into contract method calls"""
        return self.new_owner, self.threshold


def build_add_owner_with_threshold(
    safe: Safe, sub_safe: Safe, params: AddOwnerArgs
) -> MultiSendTx:
    """
    :param safe: Safe owning each of this child safes
    :param sub_safe: Safe owner by Parent with signing threshold = 1
    :param params: Arguments to be used on function call
    :return: Multisend Transaction
    """
    assert sub_safe.retrieve_is_owner(
        safe.address
    ), f"{safe} not an owner of {sub_safe}"
    print(
        f"building "
        f"addOwnerWithThreshold({params.new_owner}, {params.threshold}) "
        f"on {sub_safe.address} as MultiSendTxm from {safe.address}"
    )

    transaction = SafeTransaction(
        to=sub_safe.address,
        value=0,
        data=sub_safe.contract.encodeABI("addOwnerWithThreshold", params.as_list()),
        operation=SafeOperation.CALL,
    )
    return MultiSendTx(
        to=sub_safe.address,
        value=0,
        data=encode_exec_transaction(sub_safe, safe.address, transaction),
        operation=MultiSendOperation.CALL,
    )
