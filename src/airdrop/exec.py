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


class AirdropCommand(Enum):
    """All supported Scrip Entry point commands"""

    CLAIM = "CLAIM"
    REDEEM = "REDEEM"


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script Arguments")
    parser.add_argument(
        "--command",
        type=AirdropCommand,
        choices=list(AirdropCommand),
        required=True,
        help="Supported Airdrop Contract interactions",
    )
    args = parser.parse_args()
    parent, children = SafeFamily.from_args(parser).as_safes(CLIENT)
    if args.command == AirdropCommand.REDEEM:
        transactions = [
            build_and_sign_redeem(
                safe=parent,
                sub_safe=child,
                allocation=Allocation.from_address(child.address),
            )
            for child in children
        ]
    elif args.command == AirdropCommand.CLAIM:
        print(f"Using Parent Safe {parent.address} as Beneficiary")
        transactions = [
            build_and_sign_claim(
                safe=parent,
                sub_safe=child,
                allocation=Allocation.from_address(child.address),
                beneficiary=parent.address,
            )
            for child in children
        ]
    else:
        raise ValueError(
            f"{args.command} is not a currently supported Airdrop interface method"
        )

    nonce = multi_exec(
        parent, CLIENT, signing_key=os.environ["PROPOSER_PK"], transactions=transactions
    )
