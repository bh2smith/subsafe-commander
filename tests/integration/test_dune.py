import unittest

from web3 import Web3

from src.dune import fetch_child_safes


class MyTestCase(unittest.TestCase):
    def test_fetch_children_success(self):
        fleet = fetch_child_safes("0x20026f06342e16415b070ae3bdb3983af7c51c95", 0, 10)
        self.assertEqual(len(fleet), 6)
        expected = sorted(
            [
                *map(
                    lambda t: t.lower(),
                    [
                        "0xdc7Aa21885b82702fb410bCdcB79e2643fCA465c",
                        "0x8926c4D7F8AdA5B74827bFEa51aE60517Dde21cf",
                        "0xEEf4F29Fd2109Fca7E59A39F0A20aa377Dc4615A",
                        "0xEb3D50384Ca35624c3E9a86e522EAdB4A372fF23",
                        "0x99523Fe203262A64fdA0b0BBCaad8C85637C383a",
                        "0xe95c569aB66f4EC6863776D3E88204242d660DB0",
                    ],
                )
            ]
        )
        print(expected)
        print(fleet)
        self.assertEqual(
            list(map(lambda t: Web3().toChecksumAddress(t), expected)),
            fleet,
        )

        fleet = fetch_child_safes("0x20026f06342e16415b070ae3bdb3983af7c51c95", 3, 4)
        self.assertEqual(
            list(map(lambda t: Web3().toChecksumAddress(t), expected[3:4])),
            fleet,
        )

    def test_fetch_children_fail(self):
        with self.assertRaises(ValueError) as err:
            fetch_child_safes("0xa421e74a7ebc8f3354b7352ba7841084b701e85f", 0, 100)
        self.assertEqual(
            str(err.exception),
            "No results returned for parent 0xa421e74a7ebc8f3354b7352ba7841084b701e85f",
        )
        with self.assertRaises(ValueError) as err:
            fetch_child_safes("0xBadAddress", 0, 1)
        self.assertEqual(
            str(err.exception), "No results returned for parent 0xBadAddress"
        )


if __name__ == "__main__":
    unittest.main()
