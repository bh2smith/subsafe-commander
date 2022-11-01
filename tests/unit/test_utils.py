import unittest

from src.util import partition_array


class MyTestCase(unittest.TestCase):
    def test_something(self):
        arr = [1, 2, 3]
        self.assertEqual(partition_array(arr, 3), [arr])
        self.assertEqual(partition_array(arr, 4), [arr])
        self.assertEqual(partition_array(arr, 2), [[1, 2], [3]])
        self.assertEqual(partition_array(arr, 1), [[1], [2], [3]])
        with self.assertRaises(ValueError):
            partition_array(arr, 0)


if __name__ == "__main__":
    unittest.main()
