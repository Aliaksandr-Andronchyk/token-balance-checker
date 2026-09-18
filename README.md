# token-balance-checker

CLI tool that shows ETH and ERC-20 token balances for any Ethereum address.

It queries a public Ethereum RPC endpoint (llamarpc) to fetch the native ETH balance and calls `balanceOf` on several well-known token contracts: USDT, USDC, DAI, WETH, LINK.

## Install

```
pip install requests rich
```

Or from the requirements file:

```
pip install -r requirements.txt
```

## Usage

```
python main.py 0xYourEthereumAddressHere
```

The output is a table with token names and their balances.

## How it works

- ETH balance -- fetched via `eth_getBalance` JSON-RPC call.
- ERC-20 balances -- fetched by calling the `balanceOf(address)` function on each token contract via `eth_call`.
- No API key required -- uses a free public RPC endpoint.
