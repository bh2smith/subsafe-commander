import unittest

from eth_typing import URI, HexStr
from gnosis.eth import EthereumClient
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from web3 import Web3

from src.environment import INFURA_KEY
from src.multisend import (
    build_encoded_multisend,
    build_and_sign_multisend,
    BATCH_SIZE_LIMIT,
    partitioned_build_multisend,
)
from src.safe import get_safe
from src.token_transfer import Token, Transfer


# These tests are more related to the CSV Airdrop app since the consist of token transfers).
# TODO generalize the Multisend to beyond Token transfers.


class TestMultiSend(unittest.TestCase):
    def setUp(self) -> None:
        node_url = f"https://goerli.infura.io/v3/{INFURA_KEY}"
        self.client = EthereumClient(URI(node_url))

    def test_multisend_encoding(self):
        receiver = Web3.to_checksum_address("0xde786877a10dbb7eba25a4da65aecf47654f08ab")
        cow_token = Token("0x1111111111111111111111111111111111111111", decimals=18)
        self.assertEqual(
            build_encoded_multisend([], self.client),
            "0x8d80ff0a"  # MethodID
            "0000000000000000000000000000000000000000000000000000000000000020"
            "0000000000000000000000000000000000000000000000000000000000000000",
        )

        native_transfer = Transfer(
            token=None, receiver=receiver, amount_wei=16
        ).as_multisend_tx()
        self.assertEqual(
            build_encoded_multisend([native_transfer], self.client),
            "0x8d80ff0a"  # MethodID
            "0000000000000000000000000000000000000000000000000000000000000020"
            "0000000000000000000000000000000000000000000000000000000000000055"
            "00de786877a10dbb7eba25a4da65aecf47654f08ab0000000000000000000000"
            "0000000000000000000000000000000000000000100000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000",
        )
        erc20_transfer = Transfer(
            token=cow_token,
            receiver=receiver,
            amount_wei=15,
        ).as_multisend_tx()
        self.assertEqual(
            build_encoded_multisend([erc20_transfer], self.client),
            "0x8d80ff0a"  # MethodID
            "0000000000000000000000000000000000000000000000000000000000000020"
            "0000000000000000000000000000000000000000000000000000000000000099"
            "0011111111111111111111111111111111111111110000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000044a9059cbb00000000000000"
            "0000000000de786877a10dbb7eba25a4da65aecf47654f08ab00000000000000"
            "0000000000000000000000000000000000000000000000000f00000000000000",
        )
        self.assertEqual(
            build_encoded_multisend([erc20_transfer, native_transfer], self.client),
            "0x8d80ff0a"  # MethodID
            "0000000000000000000000000000000000000000000000000000000000000020"
            "00000000000000000000000000000000000000000000000000000000000000ee"
            "0011111111111111111111111111111111111111110000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000044a9059cbb00000000000000"
            "0000000000de786877a10dbb7eba25a4da65aecf47654f08ab00000000000000"
            "0000000000000000000000000000000000000000000000000f00de786877a10d"
            "bb7eba25a4da65aecf47654f08ab000000000000000000000000000000000000"
            "0000000000000000000000000010000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000",
        )
        self.assertEqual(
            build_encoded_multisend([native_transfer, erc20_transfer], self.client),
            "0x8d80ff0a"  # MethodID
            "0000000000000000000000000000000000000000000000000000000000000020"
            "00000000000000000000000000000000000000000000000000000000000000ee"
            "00de786877a10dbb7eba25a4da65aecf47654f08ab0000000000000000000000"
            "0000000000000000000000000000000000000000100000000000000000000000"
            "0000000000000000000000000000000000000000000011111111111111111111"
            "1111111111111111111100000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "00000000000000000044a9059cbb000000000000000000000000de786877a10d"
            "bb7eba25a4da65aecf47654f08ab000000000000000000000000000000000000"
            "000000000000000000000000000f000000000000000000000000000000000000",
        )

    def test_large_batches(self):
        client = EthereumClient(URI("https://rpc.gnosischain.com"))
        safe = get_safe("0x206a9EAa7d0f9637c905F2Bf86aCaB363Abb418c", client)
        recipient = Web3().to_checksum_address("0x".ljust(42, "0"))
        too_many_transactions = [
            MultiSendTx(
                to=recipient,
                value=0,
                data=HexStr("0x"),
                operation=MultiSendOperation.CALL,
            )
        ] * (BATCH_SIZE_LIMIT + 1)
        with self.assertRaises(RuntimeError) as err:
            build_and_sign_multisend(
                safe,
                transactions=too_many_transactions,
                client=self.client,
                signing_key="",
            )
        self.assertEqual(
            f"too many transactions for single batch "
            f"({BATCH_SIZE_LIMIT + 1}), use partitioned_build_multisend!",
            str(err.exception),
        )

        with self.assertLogs("src.multisend", level="INFO"):
            txs = partitioned_build_multisend(
                safe,
                transactions=too_many_transactions,
                client=self.client,
                signing_key="0" * 64,
            )
        self.assertEqual(len(txs), 2)


if __name__ == "__main__":
    unittest.main()
