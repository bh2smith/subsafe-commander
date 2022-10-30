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
from src.airdrop.tx import transactions_for, AirdropCommand
from src.environment import CLIENT
from src.safe import multi_exec, SafeFamily


class ExecCommand(Enum):
    """All supported Scrip Entry point commands"""

    CLAIM = "CLAIM"
    REDEEM = "REDEEM"
    ADD_OWNER = "ADD_OWNER"

    def __str__(self) -> str:
        return str(self.value)

    def is_airdrop_function(self) -> bool:
        """Returns true if command is an airdrop contract function"""
        return self in {ExecCommand.CLAIM, ExecCommand.REDEEM}

    def as_airdrop_command(self) -> AirdropCommand:
        """Converts command into AirdropCommand. fails if not"""
        return AirdropCommand(self.value)


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

    if command.is_airdrop_function():
        transactions = transactions_for(parent, children, command.as_airdrop_command())
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

    nonce = multi_exec(
        parent, CLIENT, signing_key=os.environ["PROPOSER_PK"], transactions=transactions
    )
