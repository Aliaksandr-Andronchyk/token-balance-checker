# token-balance-checker

CLI tool that shows ETH balance and top ERC-20 token balances for any Ethereum address. Uses the Etherscan public API.

## Install

```
pip install -r requirements.txt
```

## Usage

```
python balance_checker.py --address 0xYourEthereumAddress
```

With a custom Etherscan API key:

```
python balance_checker.py --address 0xYourEthereumAddress --api-key YOUR_KEY
```

Show only top 5 tokens:

```
python balance_checker.py --address 0xYourEthereumAddress --top 5
```
