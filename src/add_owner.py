"""A couple of helper methods associated with building ;nested Safe addOwnerWithThreshold method"""
import argparse
import os
from dataclasses import dataclass

from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from web3 import Web3

from src.environment import CLIENT
from src.multisend import post_safe_tx, build_and_sign_multisend
from src.safe import SafeTransaction, encode_exec_transaction, SafeFamily


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
    # Should consider using this instead of my own SafeTransaction object.
    # tx = safe.build_multisig_tx(
    #     to=MULTISEND_CONTRACT,
    #     value=0,
    #     data=encoded_multisend,
    #     operation=SafeOperation.DELEGATE_CALL.value,
    # )
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


def multi_add_owner(
    safe: Safe,
    sub_safes: list[Safe],
    params: AddOwnerArgs,
    client: EthereumClient,
    signing_key: str,
) -> int:
    """
    Iteratively builds and posts a multisend transaction adding `new_owner` to each child safe.
    Requires that `parent` is a single signer on all `children`.
    """
    print(
        f"loaded Parent Safe {safe.address}: version={parent.retrieve_version()} "
        f"along with {len(children)} child safes"
    )

    print(
        f"building an executing a MultiSend transaction consisting of calls to "
        f"addOwnerWithThreshold on each of {children}"
    )
    return post_safe_tx(
        safe_tx=build_and_sign_multisend(
            safe=safe,
            transactions=[
                build_add_owner_with_threshold(
                    safe=safe,
                    # Unfortunate thing about having this so deeply nested
                    # is that we can't log about the loaded child safes:
                    # functional programming ftw
                    sub_safe=sub_safe,
                    params=params,
                )
                for sub_safe in sub_safes
            ],
            client=client,
            signing_key=signing_key,
        ),
        tx_service=TransactionServiceApi(client.get_network()),
    )


if __name__ == "__main__":
    parent, children = SafeFamily.from_args().as_safes(CLIENT)
    parser = argparse.ArgumentParser("Add Owner Args: New Owner and threshold")
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
    args = parser.parse_args()
    multi_add_owner(
        safe=parent,
        sub_safes=children,
        params=AddOwnerArgs(
            new_owner=Web3.toChecksumAddress(args.new_owner),
            threshold=args.threshold,
        ),
        client=CLIENT,
        signing_key=os.environ["PROPOSER_PK"],
    )
