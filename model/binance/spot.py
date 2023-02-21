import logging

from ccxt import binance

from utils.trade_logger import add_log_info

trade_info = []
profit_loss = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BinanceSpot:
    def __init__(self):
        add_log_info(logger, exchange)
        self.logger = logger
        
    def trading(self):
        ...