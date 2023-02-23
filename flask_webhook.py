import logging
import os
from datetime import datetime
from threading import Thread

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

json_data_list = []
@app.route('/webhook/', methods=['POST'])
def hook():
    
    incoming_data = request.json
    json_data_list.append(incoming_data)
    
    return 'Data received'

def process_data(data):
    ex = [exchange, exchange2, exchange_d, exchange2_d]
    threads = []
    
    for incoming_data in json_data_list:
        # Do something with the data here
        t = TradeCrypto(incoming_data, ex)
        thread = Thread(target=t.run)
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to finish before returning
    for thread in threads:
        thread.join()
        
    return 'Data processed'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
