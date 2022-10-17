"""Models associated with ERC20 Tokens and Transfers"""
from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress
from gnosis.safe.multi_send import MultiSendTx, MultiSendOperation
from web3 import Web3

from src.abis.load import load_contract_abi
from src.constants import ERC20_ABI
from src.environment import CLIENT

log = logging.getLogger(__name__)

ERC20_TOKEN = CLIENT.w3.eth.contract(
    abi=load_contract_abi("erc20"),
)


@functools.cache
def get_token_decimals(address: ChecksumAddress) -> int:
    """Fetches Token Decimals and caches results by address"""
    # This requires a real web3 connection
    log.info(f"fetching decimals for token {address}")
    token_info = CLIENT.w3.eth.contract(address=address, abi=ERC20_ABI)
    # This "trick" is because of the unknown type returned from the contract call.
    token_decimals: int = token_info.functions.decimals().call()
    return token_decimals


class Token:
    """
    Token class consists of token `address` and additional `decimals` value.
    The constructor exists in a way that we can either
    - provide the decimals (for unit testing) which avoids making web3 calls
    - fetch the token decimals with eth_call.
    Since we primarily work with the COW token, the decimals are hardcoded here.
    """

    def __init__(self, address: str | ChecksumAddress, decimals: Optional[int] = None):
        if isinstance(address, str):
            address = Web3.toChecksumAddress(address)
        self.address = address
        self.decimals = (
            decimals if decimals is not None else get_token_decimals(address)
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Token):
            return self.address == other.address and self.decimals == other.decimals
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Token):
            return self.address < other.address
        return False

    def __hash__(self) -> int:
        return self.address.__hash__()


class TokenType(Enum):
    """Classifications of Airdrop Transfer Types"""

    NATIVE = "native"
    ERC20 = "erc20"

    # Technically the app also supports NFT transfers, but this is irrelevant here
    # NFT = 'nft'

    @classmethod
    def from_str(cls, type_str: str) -> TokenType:
        """Constructs Enum variant from string (case-insensitive)"""
        try:
            return cls[type_str.upper()]
        except KeyError as err:
            raise ValueError(f"No TokenType {type_str}!") from err

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Transfer:
    """Total amount reimbursed for accounting period"""

    token: Optional[Token]
    receiver: ChecksumAddress
    amount_wei: int

    @classmethod
    def from_dict(cls, obj: dict[str, str]) -> Transfer:
        """Converts Dune data dict to object with types"""
        token_address = obj.get("token_address", None)
        return cls(
            token=Token(token_address) if token_address else None,
            receiver=Web3.toChecksumAddress(obj["receiver"]),
            amount_wei=int(obj["amount"]),
        )

    @property
    def token_type(self) -> TokenType:
        """Returns the type of transfer (Native or ERC20)"""
        if self.token is None:
            return TokenType.NATIVE
        return TokenType.ERC20

    @property
    def amount(self) -> float:
        """Returns transfer amount_wei in units"""
        if self.token_type == TokenType.NATIVE:
            return self.amount_wei / int(10**18)
        # This case was handled above.
        assert self.token is not None
        return self.amount_wei / int(10**self.token.decimals)

    def as_multisend_tx(self) -> MultiSendTx:
        """Converts Transfer into encoded MultiSendTx bytes"""
        if self.token_type == TokenType.NATIVE:
            return MultiSendTx(
                operation=MultiSendOperation.CALL,
                to=self.receiver,
                value=self.amount_wei,
                data=HexStr("0x"),
            )
        if self.token_type == TokenType.ERC20:
            assert self.token is not None
            return MultiSendTx(
                operation=MultiSendOperation.CALL,
                to=str(self.token.address),
                value=0,
                data=ERC20_TOKEN.encodeABI(
                    fn_name="transfer", args=[self.receiver, self.amount_wei]
                ),
            )
        raise ValueError(f"Unsupported type {self.token_type}")

    def __str__(self) -> str:
        if self.token_type == TokenType.NATIVE:
            return f"TransferETH(receiver={self.receiver}, amount_wei={self.amount})"
        if self.token_type == TokenType.ERC20:
            return (
                f"Transfer("
                f"token_address={self.token}, "
                f"receiver={self.receiver}, "
                f"amount_wei={self.amount})"
            )
        raise ValueError(f"Invalid Token Type {self.token_type}")
