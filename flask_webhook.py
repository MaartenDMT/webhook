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
    
    incoming_data = request.get_json()
    json_data_list.append(incoming_data)
    
    process_data(json_data_list)
    
    return 'Data received'

def process_data(json_data_list:list):
    exchanges = {
        'ma_binance_usdtm': exchange, 
        'ma_binance_coinm': exchange2, 
        'de_binance_usdtm': exchange_d, 
        'de_binance_coinm': exchange2_d
    }

    
    threads = []
    print(exchanges)
    for incoming_data in json_data_list:
        # Do something with the data here
        thread = Thread(target =TradeCrypto, args=(incoming_data, exchanges))
        thread.start()
        threads.append(thread)
        json_data_list.remove(incoming_data)
        print(json_data_list)
    
    # Wait for all threads to finish before returning
    for thread in threads:
        thread.join()
        threads.remove(thread)
        
    return 'Data processed'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
