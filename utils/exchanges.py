import os

import ccxt
from dotenv import load_dotenv

path = '.env'
load_dotenv(path)

def get_exchanges() -> dict:
    exchange = ccxt.binance({
    "apiKey": os.environ.get('API_KEY'),
    "secret": os.environ.get('API_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
    
    })
    # exchange.set_sandbox_mode(True)

    exchange2 = ccxt.binancecoinm({
        "apiKey": os.environ.get('API_KEY'),
        "secret": os.environ.get('API_SECRET'),
        'enableRateLimit': True,
    })
    # exchange2.set_sandbox_mode(True)

    exchange_d = ccxt.binance({
        "apiKey": os.environ.get('D_BIN_KEY'),
        "secret": os.environ.get('D_BIN_SECRET'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
        },
    })
    # exchange.set_sandbox_mode(True)

    exchange2_d = ccxt.binancecoinm({
        "apiKey": os.environ.get('D_BIN_KEY'),
        "secret": os.environ.get('D_BIN_SECRET'),
        'enableRateLimit': True,
    })
    # exchange2.set_sandbox_mode(True)

    exchanges = {
        'ma_binance_usdtm': exchange, 
        'ma_binance_coinm': exchange2, 
        'de_binance_usdtm': exchange_d, 
        'de_binance_coinm': exchange2_d
    }

    
    return exchanges