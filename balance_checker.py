#!/usr/bin/env python3
"""CLI tool to check ETH balance and top ERC-20 token balances for an Ethereum address."""

import argparse
import sys
from collections import defaultdict
from decimal import Decimal

import requests
from rich.console import Console
from rich.table import Table

ETHERSCAN_API = "https://api.etherscan.io/api"
console = Console()


def get_eth_balance(address: str, api_key: str) -> Decimal:
    """Fetch native ETH balance for the given address."""
    resp = requests.get(
        ETHERSCAN_API,
        params={
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "1":
        console.print(f"[red]Etherscan error:[/red] {data.get('message', 'unknown')}")
        return Decimal(0)
    return Decimal(data["result"]) / Decimal(10**18)


def get_token_balances(address: str, api_key: str) -> list[dict]:
    """Derive ERC-20 token balances from transfer history.

    Returns a list of dicts sorted by balance descending, each with
    keys: symbol, name, balance, decimals, contract.
    """
    resp = requests.get(
        ETHERSCAN_API,
        params={
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "1":
        return []

    tokens: dict[str, dict] = {}
    balances: defaultdict[str, Decimal] = defaultdict(Decimal)
    addr_lower = address.lower()

    for tx in data["result"]:
        contract = tx["contractAddress"]
        decimals = int(tx.get("tokenDecimal", 18))
        value = Decimal(tx["value"]) / Decimal(10**decimals)

        if contract not in tokens:
            tokens[contract] = {
                "symbol": tx.get("tokenSymbol", "???"),
                "name": tx.get("tokenName", "Unknown"),
                "decimals": decimals,
                "contract": contract,
            }

        if tx["to"].lower() == addr_lower:
            balances[contract] += value
        if tx["from"].lower() == addr_lower:
            balances[contract] -= value

    result = []
    for contract, info in tokens.items():
        bal = balances[contract]
        if bal > 0:
            result.append({**info, "balance": bal})

    result.sort(key=lambda t: t["balance"], reverse=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check ETH and ERC-20 token balances for an Ethereum address."
    )
    parser.add_argument(
        "--address", required=True, help="Ethereum address to check"
    )
    parser.add_argument(
        "--api-key",
        default="YourApiKeyToken",
        help="Etherscan API key (default: free-tier demo key)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top tokens to display (default: 10)",
    )
    args = parser.parse_args()

    address = args.address
    if not address.startswith("0x") or len(address) != 42:
        console.print("[red]Invalid Ethereum address format.[/red]")
        sys.exit(1)

    console.print(f"\nChecking balances for [bold]{address}[/bold] ...\n")

    # ETH balance
    eth_balance = get_eth_balance(address, args.api_key)
    console.print(f"  ETH balance: [green]{eth_balance:.6f}[/green] ETH\n")

    # Token balances
    console.print("Fetching ERC-20 token transfers (this may take a moment) ...")
    tokens = get_token_balances(address, args.api_key)

    if not tokens:
        console.print("[yellow]No ERC-20 token balances found.[/yellow]")
        return

    table = Table(title=f"Top {args.top} ERC-20 Tokens")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Symbol", style="cyan bold")
    table.add_column("Name")
    table.add_column("Balance", justify="right", style="green")
    table.add_column("Contract", style="dim")

    for i, tok in enumerate(tokens[: args.top], 1):
        table.add_row(
            str(i),
            tok["symbol"],
            tok["name"],
            f"{tok['balance']:.4f}",
            tok["contract"][:10] + "...",
        )

    console.print(table)


if __name__ == "__main__":
    main()
