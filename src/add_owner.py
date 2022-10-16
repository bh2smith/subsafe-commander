"""A couple of helper methods associated with building ;nested Safe addOwnerWithThreshold method"""
import argparse
import os
from dataclasses import dataclass

from eth_typing.ethpm import URI
from eth_typing.evm import ChecksumAddress
from gnosis.eth import EthereumClient
from gnosis.safe import Safe, SafeOperation
from gnosis.safe.api import TransactionServiceApi
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from web3 import Web3

from src.environment import NODE_URL
from src.multisend import post_safe_tx, build_and_sign_multisend
from src.safe import SafeTransaction, encode_exec_transaction, get_safe


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
    parent: str,
    children: list[str],
    params: AddOwnerArgs,
    client: EthereumClient,
    signing_key: str,
) -> int:
    """
    Iteratively builds and posts a multisend transaction adding `new_owner` to each child safe.
    Requires that `parent` is a single signer on all `children`.
    """
    parent_safe = get_safe(parent, client)
    print(
        f"loaded Parent Safe {parent_safe.address}: version={parent_safe.retrieve_version()} "
        f"along with {len(children)} child safes"
    )

    print(
        f"building an executing a MultiSend transaction consisting of calls to "
        f"addOwnerWithThreshold on each of {children}"
    )
    return post_safe_tx(
        safe_tx=build_and_sign_multisend(
            safe=parent_safe,
            transactions=[
                build_add_owner_with_threshold(
                    safe=parent_safe,
                    # Unfortunate thing about having this so deeply nested
                    # is that we can't log about the loaded child safes:
                    # functional programming ftw
                    sub_safe=get_safe(child, client),
                    params=params,
                )
                for child in children
            ],
            client=client,
            signing_key=signing_key,
        ),
        tx_service=TransactionServiceApi(client.get_network()),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Add Owners To Family of Safes")
    parser.add_argument(
        "--parent",
        type=str,
        required=True,
        help="Master Safe Address (owner of all sub safes)",
    )
    parser.add_argument(
        "--new-owner",
        type=str,
        required=True,
        help="Ethereum address to be added as owner of sub-safes",
    )
    parser.add_argument(
        "--sub-safes",
        type=str,
        required=True,
        help="List of Ethereum addresses corresponding to Safes owned by parent safe",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=1,
        help="New Safe signature threshold",
    )
    args = parser.parse_args()
    multi_add_owner(
        parent=args.parent,
        children=args.sub_safes.split(","),
        params=AddOwnerArgs(
            new_owner=Web3.toChecksumAddress(args.new_owner),
            threshold=args.threshold,
        ),
        client=EthereumClient(URI(NODE_URL)),
        signing_key=os.environ["PROPOSER_PK"],
    )
