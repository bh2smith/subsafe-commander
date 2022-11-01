"""
Entry point to Execute Redeem and Claim methods of Safe Airdrop.
This script perform "multi redeem" on behalf of a family of safes.
"""
from __future__ import annotations

import argparse
import os
from enum import Enum
from itertools import chain

from web3 import Web3

from src.add_owner import build_add_owner_with_threshold, AddOwnerArgs
from src.airdrop.tx import transactions_for as airdrop_tx_for, AirdropCommand
from src.log import set_log
from src.snapshot.tx import transactions_for as snapshot_tx_for, SnapshotCommand
from src.environment import CLIENT
from src.safe import multi_exec, SafeFamily

log = set_log(__name__)


def transaction_queue(address: str) -> str:
    """URL to transaction queue"""
    return f"https://gnosis-safe.io/app/eth:{address}/transactions/queue"


class ExecCommand(Enum):
    """All supported Scrip Entry point commands"""

    CLAIM = "CLAIM"
    REDEEM = "REDEEM"
    ADD_OWNER = "ADD_OWNER"
    SET_DELEGATE = "setDelegate"
    CLEAR_DELEGATE = "clearDelegate"
    DELEGATE_REDEEM_CLAIM = "FullClaim"

    def __str__(self) -> str:
        return str(self.value)

    def is_airdrop_function(self) -> bool:
        """Returns true if command is an airdrop contract function"""
        return self in {ExecCommand.CLAIM, ExecCommand.REDEEM}

    def is_snapshot_function(self) -> bool:
        """Returns true if command is an snapshot contract function"""
        return self in {ExecCommand.SET_DELEGATE, ExecCommand.CLEAR_DELEGATE}

    def as_airdrop_command(self) -> AirdropCommand:
        """Converts command into AirdropCommand. fails if not"""
        return AirdropCommand(self.value)

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

    if command == ExecCommand.DELEGATE_REDEEM_CLAIM:
        delegates = snapshot_tx_for(
            parent, children, ExecCommand.SET_DELEGATE.as_snapshot_command()
        )
        redeems = airdrop_tx_for(
            parent, children, ExecCommand.REDEEM.as_airdrop_command()
        )
        claims = airdrop_tx_for(
            parent, children, ExecCommand.CLAIM.as_airdrop_command()
        )
        # Zip so all three items likely be batched together if transactions get partitioned
        transactions = list(chain.from_iterable(zip(delegates, redeems, claims)))
    elif command.is_airdrop_function():
        transactions = airdrop_tx_for(parent, children, command.as_airdrop_command())
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
                    new_owner=Web3.toChecksumAddress(args.new_owner),
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
