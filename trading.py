from concurrent.futures import ThreadPoolExecutor

from model.binance import coinm, margin, spot, usdtm
from tickets import tickers, tickers2coin


class TradeCrypto:
  def __init__(self, request, ex, logger) -> None:
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
    self.logger = logger
    self.multi = 2
    
    if self.symbol in ["BTCUSDT", "ETHUSDT"]:
      self.leverage = 50
      self.ProcessingMoney = 7
      self.trade()
    elif self.symbol in ["BNBUSDT", "ADAUSDT", "LINKUSDT"]:
      self.leverage = 20
      self.trade()
    elif self.symbol in ["XTZUSDT","REEFUSDT", "ROSEUSDT"]:
      self.fast_bot()
    else:
      self.trade()
      
  def __str__(self) -> str:
    return "Succeeded"  

  def fast_bot(self) -> None:
    leverage = 20
    tp1 = 6 / leverage
    tp2 = 7 / leverage 
    tp3 = 8 / leverage 
    stopLoss = 5 / leverage
    ProcessingMoney = 5
    self.execute_usdtm_trade(self.ex[0], self.symbol, self.side, self.t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, self.logger)
    
  def trade(self) -> None:
    with ThreadPoolExecutor() as executor:
      executor.submit(self.execute_usdtm_trade, self.ex[0], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney, self.logger)
      executor.submit(self.execute_coinm_trade, self.ex[1], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney*self.multi, self.logger)

  def execute_usdtm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger):
    self.usdtm = usdtm.BinanceFuturesUsdtm(exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger)
    self.logger.info(f"starting the {self.usdtm}")
  
  def execute_coinm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger):
    ttick = tickers[symbol]
    for d in tickers2coin:
        if d == ttick:
            self.logger.info(d)
            self.coinm = coinm.BinanceFuturesCoinm(exchange, d, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger)
            self.logger.info(f"starting the {self.coinm}")
        else:
          self.logger.info("No Symbol for COIN-M")

  def execute_spot_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger):
    # self.spot = spot.BinanceSpot
    pass
  
  def execute_margin_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney, logger):
    # self.margin = margin.BinanceMargin
    pass