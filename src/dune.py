"""Self contained program use of Dune Client"""
import os

from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import Query
from dune_client.types import QueryParameter
from eth_typing.evm import ChecksumAddress
from web3 import Web3


def fetch_child_safes(
    parent: str | ChecksumAddress, index_from: int, index_to: int
) -> list[ChecksumAddress]:
    """Retrieves Child Safes from Parent via Dune"""
    load_dotenv()
    dune = DuneClient(os.environ["DUNE_API_KEY"])
    results = dune.refresh(
        query=Query(
            name="Safe Families",
            query_id=1416166,
            params=[
                QueryParameter.text_type("Blockchain", "ethereum"),
                QueryParameter.text_type("ParentSafe", parent),
                QueryParameter.number_type("IndexFrom", index_from),
                QueryParameter.number_type("IndexTo", index_to),
            ],
        )
    )
    if len(results) == 0:
        raise ValueError(f"No results returned for parent {parent}")

    print(f"got fleet of size {len(results)}")
    return [Web3().toChecksumAddress(row["bracket"]) for row in results]
