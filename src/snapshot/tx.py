"""Transaction List Builder interface for exec script"""
from enum import Enum

from gnosis.safe import Safe
from gnosis.safe.multi_send import MultiSendTx

from src.log import set_log
from src.multisend import build_multisend_from_data
from src.safe import encode_exec_transaction
from src.snapshot.delegate_registry import (
    encode_set_delegate,
    SAFE_DELEGATION_ID,
    encode_clear_delegate,
)

log = set_log(__name__)


class SnapshotCommand(Enum):
    """Enum containing all callable Snapshot contract methods"""

    SET_DELEGATE = "setDelegate"
    CLEAR_DELEGATE = "clearDelegate"


def transactions_for(
    parent: Safe, children: list[Safe], command: SnapshotCommand
) -> list[MultiSendTx]:
    """Builds transaction for given Snapshot command"""

    if command == SnapshotCommand.SET_DELEGATE:
        log.info(
            f"Setting delegation for namespace {SAFE_DELEGATION_ID} to parent {parent.address}"
        )
        return [
            build_multisend_from_data(
                safe=child,
                data=encode_exec_transaction(
                    child,
                    parent.address,
                    encode_set_delegate(SAFE_DELEGATION_ID, parent.address),
                ),
            )
            for child in children
        ]

    if command == SnapshotCommand.CLEAR_DELEGATE:
        return [
            build_multisend_from_data(
                safe=child,
                data=encode_exec_transaction(
                    child,
                    parent.address,
                    encode_clear_delegate(SAFE_DELEGATION_ID),
                ),
            )
            for child in children
        ]
    raise EnvironmentError(f"Invalid snapshot command: {command}")
