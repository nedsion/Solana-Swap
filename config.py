import os
import json

class Config:
    PROGRAM_TITLE = 'Solana Wallet Helper'
    PROGRAM_VERSION = '0.1.0'

    CONFIG_PATH = 'config.json'
    DEFAULT_CONFIG = {
        'TRANSFER_MIN_SLEEP': 0.5,
        'TRANSFER_MAX_SLEEP': 2.0,
    }

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as file:
            DEFAULT_CONFIG = json.load(file)

    SOLANA_RPC_END_POINT = 'https://api.mainnet-beta.solana.com'
    DEFAULT_FORMAT = '.10f'

    


CONFIG = Config()