"""Transaction List Builder interface for exec script"""
from enum import Enum

from gnosis.safe import Safe
from gnosis.safe.multi_send import MultiSendTx

from src.airdrop.allocation import Allocation
from src.airdrop.encode import build_and_sign_redeem, build_and_sign_claim


class AirdropCommand(Enum):
    """Enum containing all callable Airdrop contract methods"""

    CLAIM = "CLAIM"
    REDEEM = "REDEEM"


def transactions_for(
    parent: Safe, children: list[Safe], command: AirdropCommand
) -> list[MultiSendTx]:
    """Builds transaction for given Airdrop command"""
    allocations: dict[Safe, list[Allocation]] = {child: [] for child in children}
    for child in children:
        try:
            allocations[child] += Allocation.from_address(child.address)
        except FileNotFoundError as err:
            print(f"Not Found: {err} - skipping!")

    transactions = []
    if command == AirdropCommand.REDEEM:
        for child, allocation_list in allocations.items():
            transactions += [
                build_and_sign_redeem(
                    safe=parent,
                    sub_safe=child,
                    allocation=allocation,
                )
                for allocation in allocation_list
                # all other tags are beyond the claim period
                if allocation.tag == 'user_v2'
            ]
        return transactions

    if command == AirdropCommand.CLAIM:
        print(f"Using Parent Safe {parent.address} as Beneficiary")
        for child, allocation_list in allocations.items():
            transactions += [
                build_and_sign_claim(
                    safe=parent,
                    sub_safe=child,
                    allocation=allocation,
                    beneficiary=parent.address,
                )
                for allocation in allocation_list
            ]

        return transactions

    raise EnvironmentError(f"Invalid airdrop command: {command}")
