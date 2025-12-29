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

    SOLANA_RPC_END_POINT = 'https://mainnet.helius-rpc.com/?api-key=86e76293-b0c2-419c-9221-ec374b14b653' # https://api.devnet.solana.com / https://api.mainnet-beta.solana.com / https://orbital-silent-slug.solana-mainnet.quiknode.pro/73978626e2fc1f198ababefcd71853c39abf3065/
    DEFAULT_FORMAT = '.10f'

    


CONFIG = Config()