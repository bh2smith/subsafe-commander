"""Loading environment variables as project constants"""
import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
SAFE_ADDRESS = Web3.toChecksumAddress(
    os.environ.get("SAFE_ADDRESS", "0xA03be496e67Ec29bC62F01a428683D7F9c204930")
)
INFURA_KEY = os.environ.get("INFURA_KEY")
NETWORK_STRING = os.environ.get("NETWORK", "mainnet")
NODE_URL = f"https://{NETWORK_STRING}.infura.io/v3/{INFURA_KEY}"
