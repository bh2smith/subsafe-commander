import unittest
from src.snapshot.delegate_registry import DelegationId


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # These are equivalent DelegationIds (one string and one hex representation)
        self.hex_value = (
            "0x736166652e657468000000000000000000000000000000000000000000000000"
        )
        self.str_value = "safe.eth"

    def test_delegation_id_from_hex(self):

        from_hex = DelegationId.from_hex(self.hex_value)
        self.assertEqual(str(from_hex), self.str_value)
        self.assertEqual(from_hex.hex, self.hex_value)

    def test_delegation_id_from_str(self):
        from_str = DelegationId.from_str(self.str_value)
        self.assertEqual(str(from_str), self.str_value)
        self.assertEqual(from_str.hex, self.hex_value)

    def test_delegation_id_equality(self):
        self.assertEqual(
            DelegationId.from_hex(self.hex_value), DelegationId.from_str(self.str_value)
        )


if __name__ == "__main__":
    unittest.main()
