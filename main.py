#!/usr/bin/env python3
"""CLI tool to check ETH and ERC-20 token balances for an Ethereum address."""

import argparse
import json
import sys

import requests
from rich.console import Console
from rich.table import Table

RPC_URL = "https://eth.llamarpc.com"

# Well-known ERC-20 tokens: name, contract address, decimals
TOKENS = [
    ("USDT",  "0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
    ("USDC",  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
    ("DAI",   "0x6B175474E89094C44Da98b954EedeAC495271d0F", 18),
    ("WETH",  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18),
    ("LINK",  "0x514910771AF9Ca656af840dff83E8264EcF986CA", 18),
]

# balanceOf(address) selector
BALANCE_OF_SELECTOR = "0x70a08231"


def rpc_call(method: str, params: list) -> dict:
    """Send a JSON-RPC call to the Ethereum node."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    resp = requests.post(RPC_URL, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data


def get_eth_balance(address: str) -> float:
    """Return ETH balance as a float."""
    data = rpc_call("eth_getBalance", [address, "latest"])
    wei = int(data["result"], 16)
    return wei / 1e18


def get_erc20_balance(token_address: str, wallet: str, decimals: int) -> float:
    """Return ERC-20 token balance by calling balanceOf on the contract."""
    # Encode the call data: selector + address padded to 32 bytes
    padded = wallet.lower().replace("0x", "").zfill(64)
    call_data = BALANCE_OF_SELECTOR + padded

    data = rpc_call("eth_call", [
        {"to": token_address, "data": call_data},
        "latest",
    ])
    raw = int(data["result"], 16)
    return raw / (10 ** decimals)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show ETH and ERC-20 token balances for an Ethereum address."
    )
    parser.add_argument("address", help="Ethereum address (0x...)")
    args = parser.parse_args()

    address = args.address
    if not address.startswith("0x") or len(address) != 42:
        print("Error: address must be a 42-character hex string starting with 0x")
        sys.exit(1)

    console = Console()

    # Fetch ETH balance
    try:
        eth_balance = get_eth_balance(address)
    except Exception as exc:
        console.print(f"[red]Failed to fetch ETH balance: {exc}[/red]")
        sys.exit(1)

    # Build table
    table = Table(title=f"Balances for {address}")
    table.add_column("Token", style="cyan")
    table.add_column("Balance", justify="right", style="green")

    table.add_row("ETH", f"{eth_balance:.6f}")

    for name, contract, decimals in TOKENS:
        try:
            balance = get_erc20_balance(contract, address, decimals)
        except Exception:
            balance = None

        if balance is not None:
            table.add_row(name, f"{balance:.6f}")
        else:
            table.add_row(name, "[red]error[/red]")

    console.print(table)


if __name__ == "__main__":
    main()
