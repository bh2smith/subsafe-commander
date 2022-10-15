"""Loading environment variables as project constants"""
import os

from dotenv import load_dotenv

load_dotenv()
NETWORK_STRING = os.environ.get("NETWORK", "gnosis")
INFURA_KEY = os.environ.get("INFURA_KEY", "EmptyInfuraKey!")

if NETWORK_STRING == "gnosis":
    BASE_NODE_URL = "https://rpc.gnosischain.com"
    NODE_URL = BASE_NODE_URL
else:
    BASE_NODE_URL = f"https://{NETWORK_STRING}.infura.io/v3"
    NODE_URL = f"{BASE_NODE_URL}/{INFURA_KEY}"

print(f"Using Base Node URL {BASE_NODE_URL}")
