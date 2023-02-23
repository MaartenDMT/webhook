import logging
import pathlib
from datetime import datetime
from time import sleep

import pandas as pd
from ccxt import binance

from model.trades.trades import Trades
from tickets import tickers, tickerscoin
from utils.trade_logger import add_log_info
from utils.util import (get_max_position_available_s, in_position_check_s,
                        start_thread)

trade_info = []
profit_loss = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BinanceSpot:
    def __init__(self, exchange: binance, symbol: str, side: int, t: int, leverage: int,
                 tp1: float, tp2: float, tp3: float, stopLoss: float, ProcessingMoney: float):

        self.takeprofit1: bool = False
        self.takeprofit2: bool = False
        self.takeprofit3: bool = False
        self.get_amount: float = 0

        add_log_info(logger, exchange)
        self.logger = logger
        self.thread = None
        self.trade_info = trade_info
        self.profit_loss = profit_loss
        self.trades = Trades(self.logger)

        self.logger.info("SPOT LOGGER ACTIVE")
        self.trading(exchange, symbol, side, t, leverage, tp1, tp2,
                     tp3, stopLoss, ProcessingMoney)

        start_thread(exchange, symbol, self.profit_loss, self.trade_info,
                     self.thread, self.logger)

    def trading(self, exchange: binance, symbol: str, side: int, t: str, leverage: int,
                tp1: float, tp2: float, tp3: float, stopLoss: float, ProcessingMoney: float):

        self.logger.info(f"exchange: {exchange.name} ")
        ticker = tickers[symbol]
        tick = tickerscoin[ticker]
        usdt_balance, ticker_balance, price = in_position_check_s(
            exchange, symbol, tick, self.logger)
        count: int = 1
        ticker_to_usdt = ticker_balance * price

        print(f"the ticker amount in usdt: {ticker_to_usdt}")

        if usdt_balance > 20 and ticker_to_usdt > 20:
            # LOAD BARS
            bars = exchange.fetch_ohlcv(
                symbol, timeframe=t, since=None, limit=30)
            df = pd.DataFrame(
                bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

            # BULL EVENT
            if side == 1:
                get_amount = get_max_position_available_s(
                    exchange, 'USDT', symbol, leverage, ProcessingMoney)
                self.logger.info(f"ENTERING LONG POSITION WITH: {get_amount}")
                l = self.trades.spot_buy(
                    exchange, symbol, get_amount, price , self.trade_info)
                
            elif side == -1:
                get_amount = get_max_position_available_s(exchange, tick, symbol, leverage, ProcessingMoney)
                self.logger.info(f"ENTERING SHORT POSITION WITH: {get_amount}")
                l = self.trades.spot_sell(exchange, symbol, get_amount, price , self.trade_info)
