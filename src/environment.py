"""Loading environment variables as project constants"""
import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
SAFE_ADDRESS = Web3.toChecksumAddress(
    os.environ.get("SAFE_ADDRESS", "0xA03be496e67Ec29bC62F01a428683D7F9c204930")
)
NETWORK_STRING = os.environ.get("NETWORK", "gnosis")


if NETWORK_STRING == "gnosis":
    BASE_NODE_URL = f"https://rpc.gnosischain.com"
    NODE_URL = BASE_NODE_URL
else:
    INFURA_KEY = os.environ.get("INFURA_KEY")
    BASE_NODE_URL = f"https://{NETWORK_STRING}.infura.io/v3"
    NODE_URL = f"{BASE_NODE_URL}/{INFURA_KEY}"

print(f"Using Base Node URL {BASE_NODE_URL}")
