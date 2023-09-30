"""Self-contained programmatic use of Dune Client"""
import os

from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dune_client.types import QueryParameter
from eth_typing.evm import ChecksumAddress
from web3 import Web3


def fetch_child_safes(
    parent: str | ChecksumAddress, index_from: int, index_to: int
) -> list[ChecksumAddress]:
    """Retrieves Child Safes from Parent via Dune"""
    load_dotenv()
    dune = DuneClient(os.environ["DUNE_API_KEY"])
    parameters = [
        QueryParameter.text_type("Blockchain", "ethereum"),
        QueryParameter.text_type("ParentSafe", parent),
        QueryParameter.number_type("IndexFrom", index_from),
        QueryParameter.number_type("IndexTo", index_to),
    ]
    results = dune.refresh(
        query=QueryBase(
            name="Safe Families",
            query_id=1416166,
            params=parameters,
        )
    ).get_rows()
    if len(results) == 0:
        raise ValueError(f"No results returned for parent {parent}")

    print(f"got fleet of size {len(results)}")
    return [Web3().to_checksum_address(row["bracket"]) for row in results]
