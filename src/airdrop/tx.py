"""Transaction List Builder interface for exec script"""

from gnosis.safe import Safe
from gnosis.safe.multi_send import MultiSendTx

from src.airdrop.allocation import Allocation
from src.airdrop.encode import build_and_sign_claim


def transactions_for(parent: Safe, children: list[Safe]) -> list[MultiSendTx]:
    """Builds transaction for given Airdrop command"""
    allocations: dict[Safe, list[Allocation]] = {child: [] for child in children}
    for child in children:
        try:
            allocations[child] += Allocation.from_address(child.address)
        except FileNotFoundError as err:
            print(f"Not Found: {err} - skipping!")

    transactions = []

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
