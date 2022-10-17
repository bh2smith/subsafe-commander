"""
Entry point to Execute Redeem and Claim methods of Safe Airdrop.
This script perform "multi redeem" on behalf of a family of safes.
"""
from __future__ import annotations

import argparse
import os
from enum import Enum

from src.airdrop.allocation import Allocation
from src.airdrop.encode import build_and_sign_redeem, build_and_sign_claim
from src.environment import CLIENT
from src.safe import multi_exec, SafeFamily


class Command(Enum):
    """All supported Scrip Entry point commands"""

    CLAIM = "CLAIM"
    REDEEM = "REDEEM"

    def __str__(self) -> str:
        return str(self.value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script Arguments")
    parser.add_argument(
        "--command",
        type=Command,
        choices=list(Command),
        required=True,
        help="Supported Airdrop Contract interactions",
    )

    parent, children = SafeFamily.from_args(parser).as_safes(CLIENT)
    args = parser.parse_args()
    allocations = {}
    for child in children:
        try:
            allocations[child] = Allocation.from_address(child.address)
        except FileNotFoundError as err:
            print(f"Not Found: {err} - skipping!")

    if args.command == Command.REDEEM:
        transactions = [
            build_and_sign_redeem(
                safe=parent,
                sub_safe=child,
                allocation=allocation,
            )
            for child, allocation in allocations.items()
        ]

    elif args.command == Command.CLAIM:
        print(f"Using Parent Safe {parent.address} as Beneficiary")
        transactions = [
            build_and_sign_claim(
                safe=parent,
                sub_safe=child,
                allocation=allocation,
                beneficiary=parent.address,
            )
            for child, allocation in allocations.items()
        ]

    else:
        raise ValueError(
            f"{args.command} is not a currently supported Airdrop interface method"
        )

    nonce = multi_exec(
        parent, CLIENT, signing_key=os.environ["PROPOSER_PK"], transactions=transactions
    )
