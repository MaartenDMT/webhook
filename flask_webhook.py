import logging
import os
from datetime import datetime

import ccxt
from dotenv import load_dotenv
from flask import Flask, request

from trading import TradeCrypto

path = '.env'
load_dotenv(path)

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


thread = None
app = Flask(__name__)


@app.route('/webhook/', methods=['POST'])
def hook():
    print(request.json)
    ex = [exchange, exchange2]

    t = TradeCrypto(request, ex)
    content = t.__str__()

    return content





if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
