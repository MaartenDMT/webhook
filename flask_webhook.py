import logging
import os
import threading
from datetime import datetime

import ccxt
from dotenv import load_dotenv
from flask import Flask, request

from trading import TradeCrypto

path='.env'
load_dotenv(path)

exchange = ccxt.binance({
    "apiKey": os.environ.get('API_KEY'),
    "secret": os.environ.get('API_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
})
#exchange.set_sandbox_mode(True)

exchange2 = ccxt.binancecoinm({
    "apiKey": os.environ.get('API_KEY'),
    "secret": os.environ.get('API_SECRET'),
    'enableRateLimit': True,
})
#exchange2.set_sandbox_mode(True)    

thread = None
app = Flask(__name__)

@app.route('/webhook/', methods=['POST'])
def hook():
    print(request.json)
    ex = [exchange, exchange2]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    add_log_info(logger)
    
    t = TradeCrypto(request, ex, logger)
    start_thread(t, thread, logger)
    
    content = t.__str__()
    logger.info(content)
    
    return content


def start_thread(tc: TradeCrypto, thread, logger) -> None:
    # check if the thread is already running
    if thread and thread.is_alive():
        logger.info("Thread is already running")
        return
      
    try:      
      logger.info("starting thread !")
      thread = threading.Thread(target=tc.update_profit_thread).start()    # start a new thread if no thread is currently running
    except Exception as e:
      logger.error(e)

def add_log_info(logger) -> None:
    file = r'data/logs/'
    time_stamp = datetime.now()  # - dt.timedelta(hours=6)
    time_stamp = time_stamp.strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(f'{file}{time_stamp}.log')
    # create a stream handler to log to the console
    stream_handler = logging.StreamHandler()
    # create a formatter for the log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add the formatter to the handlers
    if not logger.handlers:
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
