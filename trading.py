import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from os import path

import ccxt
from dotenv import load_dotenv

from model.binance import coinm, margin, spot, usdtm
from tickets import tickers, tickers2coin
from utils.trade_logger import add_log_info

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

path = '.env'
load_dotenv(path)


class TradeCrypto:
    def __init__(self, request, ex) -> None:
        self.data = request
        self.symbol = self.data['ticker']
        self.side = self.data['side']
        self.t = self.data['time']
        self.leverage = 12
        self.tp1 = 4 / (self.leverage / 2)
        self.tp2 = 6 / (self.leverage / 2)
        self.tp3 = 8 / (self.leverage / 2)
        self.stopLoss = 4 / (self.leverage / 2)
        self.ProcessingMoney = 25
        self.ex = ex
        add_log_info(logger, "main")
        self.logger = logger
        self.multi = 2

        if self.symbol in ["BTCUSDT", "ETHUSDT"]:
            self.leverage = 50
            self.ProcessingMoney = 7
            self.trade()
        elif self.symbol in ["BNBUSDT", "ADAUSDT", "LINKUSDT"]:
            self.leverage = 20
            self.trade()
        elif self.symbol in ["XTZUSDT", "REEFUSDT", "ROSEUSDT"]:
            self.fast_bot()
        elif self.symbol in ["TRXUSDT"]:
            leverage = 1
            self.execute_spot_trade(self.ex, self.symbol, self.side, self.t, leverage,
                                    self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
        else:
            self.trade()

    def __str__(self) -> str:
        return "Succeeded"

    # executing the params for the fast bot
    def fast_bot(self) -> None:
        leverage = 20
        tp1 = 6 / leverage
        tp2 = 7 / leverage
        tp3 = 8 / leverage
        stopLoss = 5 / leverage
        ProcessingMoney = 5
        self.execute_usdtm_trade(self.ex[0], self.symbol, self.side, self.t,
                                 leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)
        self.logger.info(f"starting the fastbot with symbol {self.symbol}")

    # executing all the trading in a threadpool so it is happening in parralell
    def trade(self) -> None:
        with ThreadPoolExecutor() as executor:
            executor.submit(self.execute_usdtm_trade, self.ex[0], self.symbol, self.side, self.t,
                            self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
            executor.submit(self.execute_coinm_trade, self.ex[1], self.symbol, self.side, self.t, self.leverage,
                            self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney*self.multi)
            executor.submit(self.execute_usdtm_trade, self.ex[2], self.symbol, self.side, self.t,
                            self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
            executor.submit(self.execute_coinm_trade, self.ex[3], self.symbol, self.side, self.t, self.leverage,
                            self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)

    # executing the usdtm futures
    def execute_usdtm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                            stopLoss, ProcessingMoney) -> None:
        self.usdtm = usdtm.BinanceFuturesUsdtm(exchange, symbol, side, t, leverage,
                                               tp1, tp2, tp3, stopLoss, ProcessingMoney)
        self.logger.info(f"starting the {self.usdtm}")

    # executing the coinm futures
    def execute_coinm_trade(self, exchange, symbol, side, t, leverage,
                            tp1, tp2, tp3, stopLoss, ProcessingMoney) -> None:
        ttick = tickers[symbol]
        for d in tickers2coin:
            if d == ttick:
                self.logger.info(d)
                self.coinm = coinm.BinanceFuturesCoinm(
                    exchange, d, side, t, leverage, tp1, tp2, tp3,
                    stopLoss, ProcessingMoney)
                self.logger.info(f"starting the {self.coinm}")

    # executing spot trading
    def execute_spot_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                           stopLoss, ProcessingMoney) -> None:
        self.spot = spot.BinanceSpot(exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                                     stopLoss, ProcessingMoney)

    # execute the margin trading

    def execute_margin_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                             stopLoss, ProcessingMoney) -> None:
        # self.margin = margin.BinanceMargin
        pass


if __name__ == '__main__':
    exchange = ccxt.binance({
        "apiKey": os.environ.get('API_KEY_TEST_S'),
        "secret": os.environ.get('API_SECRET_TEST_S'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        },
    })
    exchange.set_sandbox_mode(True)
    # exchange.load_markets()

    s = {
        "ticker": "TRXUSDT",
        "side": 1,
        "time": "30m"
    }
    
    tester = TradeCrypto(s, exchange)
    print(tester.__str__())
