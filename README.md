# Solana Wallet Helper

A PyQt5-based desktop application for managing Solana wallets and performing token operations on the Solana blockchain, including SOL and SPL token transfers, and Raydium DEX swap functionality.

## Features

- **Wallet Management**: Import and manage multiple Solana wallets using private keys
- **SOL Transfers**: Send SOL between wallets with configurable amounts
- **Token Transfers**: Transfer SPL tokens between wallets
- **Raydium Swap Integration**: Buy and sell tokens on Raydium DEX
- **Batch Operations**: Process multiple wallets simultaneously with configurable delays
- **Balance Checking**: View SOL and token balances for all wallets
- **GUI Interface**: User-friendly PyQt5-based interface with tabs for different operations

## Prerequisites

- Python 3.8 or higher
- Solana RPC endpoint (Mainnet/Devnet)
- Valid Solana private keys (base58 encoded)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nedsion/Solana-Swap.git
cd Solana-Swap
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your RPC endpoint in `config.py`:
```python
SOLANA_RPC_END_POINT = 'your-rpc-endpoint-here'
```

## Dependencies

- **PyQt5**: GUI framework
- **solana**: Solana Python SDK
- **solders**: Solana Rust SDK bindings
- **spl-token**: SPL token library
- **pandas**: Data manipulation
- **requests**: HTTP library
- **base58**: Base58 encoding/decoding

See `requirements.txt` for complete list with versions.

## Usage

### Starting the Application

Run the main application:
```bash
python main.py
```

### Main Features

#### 1. Transfer Operations
- **From Main Wallet**: Distribute SOL or tokens from a main wallet to multiple sub-wallets
- **To Main Wallet**: Collect SOL or tokens from multiple wallets to a main wallet
- Configure sleep time between transactions (min/max range)
- Supports both SOL and SPL token transfers

#### 2. Raydium Swap
- **Buy Tokens**: Swap SOL for tokens on Raydium DEX
- **Sell Tokens**: Swap tokens back to SOL
- Specify token contract addresses
- Configure slippage tolerance and swap amounts
- Batch swap operations across multiple wallets

#### 3. Wallet Management
- Import wallets via CSV files or manual entry
- View wallet addresses and balances
- Export wallet information
- Support for associated token accounts

### Configuration

Edit `config.py` to customize:
- `SOLANA_RPC_END_POINT`: Your Solana RPC URL
- `TRANSFER_MIN_SLEEP`: Minimum delay between transactions (seconds)
- `TRANSFER_MAX_SLEEP`: Maximum delay between transactions (seconds)
- `DEFAULT_FORMAT`: Number format for display

### CSV File Format

For bulk wallet operations, prepare CSV files with the following format:

**For transfers:**
```csv
private_key,amount
your_base58_private_key_1,0.1
your_base58_private_key_2,0.2
```

**For swaps:**
```csv
private_key,amount
your_base58_private_key_1,0.05
your_base58_private_key_2,0.1
```

## Project Structure

```
.
├── main.py              # Main application entry point
├── config.py            # Configuration settings
├── constants.py         # Solana constants (program IDs, etc.)
├── helper.py            # Core functionality (Transfer, RaydiumSwap classes)
├── worker.py            # Background worker threads
├── utils.py             # Utility functions (pool keys, swap instructions)
├── layouts.py           # Solana account layouts
├── raydium.py           # Raydium DEX integration
├── requirements.txt     # Python dependencies
├── pool_keys.json       # Cached pool keys
└── output/              # Output directory for logs/exports
```

## Key Components

### Helper Classes

- **Transfer**: Handles SOL and SPL token transfers
  - `transfer_sol()`: Transfer SOL between wallets
  - `transfer_token()`: Transfer SPL tokens
  - `get_sol_balance()`: Check SOL balance
  - `get_token_balance()`: Check token balance

- **RaydiumSwap**: Manages Raydium DEX swaps
  - `buy()`: Buy tokens with SOL
  - `sell()`: Sell tokens for SOL
  - Pool key fetching and caching

### Worker Threads

- **Worker_Transfer**: Background thread for transfer operations
- **Worker_RaydiumSwap**: Background thread for swap operations

## Security Notes

⚠️ **Important Security Considerations:**

1. **Private Keys**: Never share your private keys. Store them securely.
2. **RPC Endpoint**: Use your own RPC endpoint or a trusted provider.
3. **Test First**: Always test with small amounts on devnet before mainnet.
4. **API Keys**: Remove or replace any API keys before committing to public repositories.

## Configuration Tips

1. **RPC Performance**: Use a reliable RPC provider (Helius, QuickNode, etc.) for better performance
2. **Sleep Times**: Adjust sleep ranges to avoid rate limiting
3. **Compute Units**: Modify `UNIT_PRICE` and `UNIT_BUDGET` in `constants.py` for transaction priority
4. **Slippage**: Configure slippage tolerance based on token liquidity

## Troubleshooting

### Common Issues

1. **"Invalid private key or network error"**
   - Verify private key format (base58)
   - Check RPC endpoint connectivity

2. **"Balance is not enough"**
   - Ensure sufficient SOL for transaction fees
   - Verify token balance before transfers

3. **"No pool keys found"**
   - Verify token contract address
   - Ensure token has liquidity on Raydium

4. **Transaction Failures**
   - Increase compute units in `constants.py`
   - Adjust priority fees for faster confirmation

## Development

### Running Tests

```bash
python _test.py
```

### Building from Source

The application uses PyQt5 for the GUI. To modify the interface:
1. Edit layouts in `layouts.py`
2. Modify UI components in `main.py`
3. Test changes with `python main.py`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is provided as-is for educational purposes. Use at your own risk.

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves risk. Always:
- Do your own research
- Test thoroughly on devnet first
- Never invest more than you can afford to lose
- Be aware of gas fees and slippage

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

## Version

Current version: **0.1.0**

## Acknowledgments

- Solana Foundation for the Solana blockchain
- Raydium for DEX infrastructure
- Python Solana libraries maintainers
