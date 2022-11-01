"""Transaction List Builder interface for exec script"""
from enum import Enum

from gnosis.safe import Safe
from gnosis.safe.multi_send import MultiSendTx
from web3 import Web3

from src.log import set_log
from src.multisend import build_multisend_from_data
from src.safe import encode_exec_transaction, encode_contract_method
from src.snapshot.delegate_registry import (
    SAFE_DELEGATION_ID,
    DELEGATION_CONTRACT,
)

log = set_log(__name__)


class SnapshotCommand(Enum):
    """Enum containing all callable Snapshot contract methods"""

    SET_DELEGATE = "setDelegate"
    CLEAR_DELEGATE = "clearDelegate"

    def __str__(self) -> str:
        return str(self.value)


def transactions_for(
    parent: Safe, children: list[Safe], command: SnapshotCommand
) -> list[MultiSendTx]:
    """Builds transaction for given Snapshot command"""

    if command == SnapshotCommand.SET_DELEGATE:
        delegate = input(f"Delegate Address(default={parent.address}): ")
        if delegate != "":
            try:
                delegate = Web3().toChecksumAddress(delegate)
            except ValueError as err:
                raise ValueError(f'Invalid Delegate address "{delegate}"') from err
        else:
            delegate = parent.address
        log.info(f"Setting delegation for namespace {SAFE_DELEGATION_ID} to {delegate}")
        params = [SAFE_DELEGATION_ID.hex, delegate]
    elif command == SnapshotCommand.CLEAR_DELEGATE:
        params = [SAFE_DELEGATION_ID.hex]
    else:
        raise EnvironmentError(f"Invalid snapshot command: {command}")

    return [
        build_multisend_from_data(
            safe=child,
            data=encode_exec_transaction(
                child,
                parent.address,
                encode_contract_method(DELEGATION_CONTRACT, str(command), params),
            ),
        )
        for child in children
    ]
