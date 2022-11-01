"""Some reusable generic helper functions"""
from typing import Any


def partition_array(arr: list[Any], part_size: int) -> list[list[Any]]:
    """Partitions array into parts of size `part_size`"""
    if part_size <= 0:
        raise ValueError(f"Can't partition array into parts of size {part_size}")
    return [arr[i : i + part_size] for i in range(0, len(arr), part_size)]
