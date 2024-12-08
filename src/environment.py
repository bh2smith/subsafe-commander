"""Loading environment variables as project constants"""
import os

from dotenv import load_dotenv
from eth_typing import URI
from gnosis.eth import EthereumClient

load_dotenv()
NODE_URL = os.environ.get("NODE_URL", "https://rpc.ankr.com/eth")
if not NODE_URL:
    raise EnvironmentError("NODE_URL not set")

CLIENT = EthereumClient(URI(NODE_URL))
print("Using network", CLIENT.get_network())