"""
Entry point to Execute Redeem and Claim methods of Safe Airdrop.
This script perform "multi redeem" on behalf of a family of safes.
"""
from __future__ import annotations

import argparse
import os
from enum import Enum

from web3 import Web3

from src.add_owner import build_add_owner_with_threshold, AddOwnerArgs
from src.airdrop.tx import transactions_for as claim_tx
from src.log import set_log
from src.snapshot.tx import transactions_for as snapshot_tx_for, SnapshotCommand
from src.environment import CLIENT
from src.safe import multi_exec, SafeFamily

log = set_log(__name__)


def transaction_queue(address: str) -> str:
    """URL to transaction queue"""
    return f"https://app.safe.global/transactions/queue?safe=eth:{address}"


class ExecCommand(Enum):
    """All supported Scrip Entry point commands"""

    CLAIM = "CLAIM"
    ADD_OWNER = "ADD_OWNER"
    SET_DELEGATE = "setDelegate"
    CLEAR_DELEGATE = "clearDelegate"

    def __str__(self) -> str:
        return str(self.value)

    def is_snapshot_function(self) -> bool:
        """Returns true if command is a snapshot contract function"""
        return self in {ExecCommand.SET_DELEGATE, ExecCommand.CLEAR_DELEGATE}

    def as_snapshot_command(self) -> SnapshotCommand:
        """Converts command into SnapshotCommand. fails if not"""
        return SnapshotCommand(self.value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script Arguments")
    parser.add_argument(
        "--command",
        type=ExecCommand,
        choices=list(ExecCommand),
        required=True,
        help="Supported Airdrop Contract interactions",
    )

    parent, children = SafeFamily.from_args(parser).as_safes(CLIENT)
    args, _ = parser.parse_known_args()
    command: ExecCommand = args.command

    if command == ExecCommand.CLAIM:
        transactions = claim_tx(parent, children)
    elif command.is_snapshot_function():
        transactions = snapshot_tx_for(parent, children, command.as_snapshot_command())
    elif command == ExecCommand.ADD_OWNER:
        parser = argparse.ArgumentParser("Add Owner Arguments")
        parser.add_argument(
            "--new-owner",
            type=str,
            required=True,
            help="Ethereum address to be added as owner of sub-safes",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=1,
            help="New Safe signature threshold",
        )
        args, _ = parser.parse_known_args()
        transactions = [
            build_add_owner_with_threshold(
                safe=parent,
                sub_safe=child,
                params=AddOwnerArgs(
                    new_owner=Web3.to_checksum_address(args.new_owner),
                    threshold=args.threshold,
                ),
            )
            for child in children
        ]
    else:
        raise ValueError(
            f"{args.command} is not a currently supported Exec interface method"
        )

    nonces = multi_exec(
        parent, CLIENT, signing_key=os.environ["PROPOSER_PK"], transactions=transactions
    )
    log.info(
        f"Transaction with nonce(s) {nonces} posted to {transaction_queue(parent.address)}"
    )
