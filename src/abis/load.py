"""Basic Contract ABI loader (from json files)"""
import json
from typing import Any


def load_contract_abi(abi_name: str) -> Any:
    """Loads a contract abi from json file"""
    with open(f"src/abis/{abi_name}.json", "r", encoding="utf-8") as file:
        return json.load(file)
