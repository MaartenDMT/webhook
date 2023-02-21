import logging
from concurrent.futures import ThreadPoolExecutor

from model.binance import coinm, margin, spot, usdtm
from tickets import tickers, tickers2coin
from utils.trade_logger import add_log_info
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TradeCrypto:
    def __init__(self, request, ex) -> None:
        self.data = request.get_json()
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
        else:
            self.trade()

    def __str__(self) -> str:
        return "Succeeded"

    #executing the params for the fast bot
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

    #executing all the trading in a threadpool so it is happening in parralell
    def trade(self) -> None:
        with ThreadPoolExecutor() as executor:
            executor.submit(self.execute_usdtm_trade, self.ex[0], self.symbol, self.side, self.t,
                            self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
            executor.submit(self.execute_coinm_trade, self.ex[1], self.symbol, self.side, self.t, self.leverage,
                            self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney*self.multi)

    
    #executing the usdtm futures
    def execute_usdtm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, 
                            stopLoss, ProcessingMoney, logger) -> None:
        self.usdtm = usdtm.BinanceFuturesUsdtm(exchange, symbol, side, t, leverage,
                                               tp1, tp2, tp3, stopLoss, ProcessingMoney)
        self.logger.info(f"starting the {self.usdtm}")

    #executing the coinm futures
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

    #executing spot trading
    def execute_spot_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                           stopLoss, ProcessingMoney) -> None:
        # self.spot = spot.BinanceSpot
        pass
      
    #execute the margin trading
    def execute_margin_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3,
                             stopLoss, ProcessingMoney)-> None:
        # self.margin = margin.BinanceMargin
        pass
