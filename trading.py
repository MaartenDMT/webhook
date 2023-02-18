import csv
import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import ccxt
from ccxt.base.errors import InsufficientFunds 
import pandas as pd

from tickets import tickers, tickers2coin, tickerscoin


class TradeCrypto:
  def __init__(self, request, ex, logger):
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
    self.trade_info = []
    self.profit_loss = {}
    self.thread = None
    
    if self.symbol in ["BTCUSDT", "ETHUSDT"]:
      self.leverage = 50
      self.trade()
    elif self.symbol in ["BNBUSDT", "ADAUSDT", "LINKUSDT"]:
      self.leverage = 20
      self.trade()
    elif self.symbol in ["XTZUSDT","REEFUSDT", "ROSEUSDT"]:
      self.fast_bot()
    else:
      self.trade()
      

    self.start_thread(self.symbol)

  def start_thread(self, symbol) -> None:
    # check if the thread is already running
    if self.thread and self.thread.is_alive():
        self.logger.info("Thread is already running")
        return
      
    # start a new thread if no thread is currently running
    self.thread = threading.Thread(target=self.update_profit_thread, daemon=True).start()

  def __str__(self) -> str:
    return "Succeeded"  

  def fast_bot(self) -> None:
    leverage = 20
    tp1 = 6 / leverage
    tp2 = 7 / leverage 
    tp3 = 8 / leverage 
    stopLoss = 5 / leverage
    ProcessingMoney = 5
    self.usdtm(self.ex[0], self.symbol, self.side, self.t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)
    
  def trade(self):
    with ThreadPoolExecutor() as executor:
      executor.submit(self.execute_usdtm_trade, self.ex[0], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
      executor.submit(self.execute_coinm_trade, self.ex[1], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney*self.multi)

  def execute_usdtm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    self.usdtm(exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)

  def execute_coinm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    

    ttick = tickers[symbol]
    for d in tickers2coin:
        if d == ttick:
            self.logger.info(d)
            self.coinm(exchange, d, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)
    
    # # read the symbols from the CSV file
    # with open("coinm.csv") as file:
    #     reader = csv.reader(file)
    #     next(reader)  # skip the header row
    #     tickers2 = [row[0] for row in reader]
    
    # # read the symbols from the CSV file
    # with open("usdm.csv") as file:
    #     reader = csv.reader(file)
    #     next(reader)  # skip the header row
    #     ticker = [row[0] for row in reader]
    
    # ticker = ticks.tickers   
    # ttick = ticker[symbol]
    # for d in tickers2:
    #     if d == ttick:
    #         self.logger.info(d)
    #         self.coinm(exchange, d, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)


  def usdtm(self, exchange, symbol, side, t, leverage,tp1,tp2, tp3,stopLoss,ProcessingMoney):
    self.logger.info(f"exchange: {exchange.name} ")
    takeprofit1 = False
    takeprofit2 = False
    takeprofit3 = False
    get_amount = 0
      
    inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol,None)
    count=1

    if inPosition == False:
      exchange.fapiPrivate_post_leverage({"symbol": symbol, "leverage": leverage, })
    if symbol == "WAVESUSDT":
      exchange.fapiPrivate_post_leverage({"symbol": symbol, "leverage": 8, })

    while False or ((longPosition == False and side ==1) or (shortPosition == False and side == -1)):
      # LOAD BARS
      bars = exchange.fetch_ohlcv(symbol, timeframe=t, since=None, limit=30)
      df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

      # BULL EVENT
      if longPosition == False and side == 1:
        exchange.cancel_all_orders(symbol)
        if shortPosition:
          self.logger.info("usdtm - EXIT SHORT POSITION...")
          amount = float(position_info["positionAmt"][len(position_info.index) - 1])
          self.logger.info(f"usdtm - Amount Short Exit Position: {amount}")

          self.shortExit(exchange,symbol, amount)

          inPosition = False
          shortPosition = False

        get_amount = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
        self.logger.info(f"usdtm - ENTERING LONG POSITION WITH: {get_amount}")

        l = self.longEnter(exchange,symbol, get_amount)
        takeprofit1 = False
        takeprofit2 = False
        takeprofit3 = False
        if l == False:
          break
        if l:
          longPosition = True
        ticker = symbol
        message = "usdtm - LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
        content = f"Subject: {ticker}\n{message}"
        self.logger.info(content)
        self.logger.info("============================")

        inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol, None)
        
        if longPosition:
          # STOP LOSS FOR LONG POSITION
          self.logger.info("usdtm -SETTING STOPLOSS FOR LONG POSITION")
          get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])
          #longExit(get_amount)
          entryprice = float(position_info["entryPrice"])
          entrylow = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100
          self.logger.info(f"usdtm - entryprice: {entryprice}")
          self.logger.info(f"usdtm - entry - price: {entrylow}")
          stop = entryprice / (1+stopLoss/100) #float(entryprice - (entrylow * stopLoss))
          self.logger.info(f"usdtm - stoploss: {stop}")
          self.stoplossLong(exchange,symbol, stop, get_amount)
          ticker = symbol
          message = f"usdtm - LONG EXIT (STOP LOSS): {get_amount}\n" + "Total Money: " + \
              str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info(position_info)
          self.logger.info("============================")
          
          get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])/ 3

          if takeprofit1 == False:
            # TAKE PROFIT FOR LONG POSITION
            # TAKE PROFIT 1
            self.logger.info("usdtm - TAKE PROFIT 1")

            takep1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100* tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])
            self.takeProfitLong1(exchange,symbol, get_amount, takep1)
            takeprofit1 = True
            ticker = symbol
            message = f"usdtm - LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")


          if takeprofit2 == False:

            # TAKE PROFIT 2
            self.logger.info("usdtm - TAKE PROFIT 2")
            takep2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
            self.takeProfitLong2(exchange,symbol, get_amount, takep2)
            takeprofit2 = True
            ticker = symbol
            message = f"usdtm -LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")

          if takeprofit3 == False:

            # TAKE PROFIT 3
            self.logger.info("usdtm - TAKE PROFIT 3")
            takep3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3 + float(position_info["entryPrice"][len(position_info.index) - 1])
            takeprofit3= self.trailing_market(exchange,symbol, get_amount, takep3, 'sell')
            ticker = symbol
            message = f"usdtm - LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")


      # BEAR EVENT
      elif shortPosition == False and side == -1:
          exchange.cancel_all_orders(symbol)
          if longPosition:
            self.logger.info("usdtm - EXIT LONG POSITION...")
            amount = float(position_info["positionAmt"][len(position_info.index) - 1])
            self.logger.info(f"Amount Long Exit Position: {amount}")
            self.longExit(exchange,symbol, amount)
            inPosition = False
            longPosition = False

          get_amount = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
          self.logger.info(f"usdtm - ENTERING SHORT POSITION...: {get_amount}")
          s = self.shortEnter(exchange,symbol, get_amount)
          takeprofit1 = False
          takeprofit2 = False
          takeprofit3 = False
          if s == False:
            break
          if s:
            shortPosition = True
          ticker = symbol
          message = "usdtm - LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
          self.logger.info(position_info)
          self.logger.info("============================")

      inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol, None)
      
      sleep(0.3)
      if shortPosition:
        # STOP LOSS FOR SHORT POSITION
        self.logger.info("usdtm - SETTING STOPLOSS FOR SHORT POSITION")
        get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) * -1
        #shortExit(get_amount)
        stop = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])
        self.logger.info(f"usdtm - STOPLOSS Short: {stop}")
        self.stoplossShort(exchange,symbol, stop, get_amount)
        ticker = symbol
        message = "usdtm - LONG EXIT (STOP LOSS)\n" + "Total Money: " + \
            str(balance['total']["USDT"])
        content = f"Subject: {ticker}\n{message}"
        self.logger.info(content)
        self.logger.info(position_info)
        self.logger.info("============================")

        get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) / (3 *-1)
        # TAKE PROFIT FOR SHORT POSITION
        # TAKE PROFIT 1
        if takeprofit1 == False:
          self.logger.info("usdtm - TAKE PROFIT 1")
          
          takeps1 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp1
          takeprofit3 =self.takeProfitShort1(exchange,symbol, get_amount, takeps1)
          takeprofit1 = True
          ticker = symbol
          message = f"usdtm - LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
              "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")



        # TAKE PROFIT 2
        if takeprofit2 == False:
          self.logger.info("usdtm - TAKE PROFIT 2")
          takeps2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
              float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
          takeprofit3 =self.takeProfitShort2(exchange,symbol, get_amount, takeps2)
          takeprofit2 = True
          ticker = symbol
          message = f"usdtm - LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
              "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        # TAKE PROFIT 3
        if takeprofit3 == False:
          self.logger.info("usdtm - TAKE PROFIT 3")
          takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp3
          takeprofit3 = self.trailing_market(exchange,symbol, get_amount, takeps3, 'buy')
          ticker = symbol
          message = f"usdtm - LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
              "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

      if inPosition == False:
        self.logger.info("NO POSITION YET...")
        self.logger.info("============================")
        
      count +=1

      
      if count == 3:
        break 
      
      inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol, None)


      if shortPosition:
        self.logger.info("usdtm - IN A SHORT POSITION WITH:")
        self.logger.info("usdtm - STOP LOSS PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])))
        self.logger.info("usdtm - TAKE PROFIT 1 PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1))
        self.logger.info("usdtm - TAKE PROFIT 2 PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2))
        self.logger.info("usdtm - TAKEPROFIT 1 is - {}",(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1))
        self.logger.info("usdtm - TAKEPROFIT 2 is - {}",(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2))
        self.logger.info("usdtm - TAKEPROFIT 3 is - {}",(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3))


      elif longPosition:
        self.logger.info("usdtm - IN A LONG POSITION WITH: ")
        self.logger.info("usdtm - PRICE: {}", (float(df["close"][len(df.index)-1])))
        self.logger.info("usdtm - STOP LOSS PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss))
        self.logger.info("usdtm - TAKE PROFIT 1 PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])))
        self.logger.info("usdtm - TAKE PROFIT 2 PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])))
        self.logger.info("usdtm - TAKEPROFIT 1 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1))
        self.logger.info("usdtm - TAKEPROFIT 2 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2))
        self.logger.info("usdtm - TAKEPROFIT 3 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3))

  #COIN- M
  def coinm(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    self.logger.info(f"exchange: {exchange.name} ")
    takeprofit1 = False
    takeprofit2 = False
    takeprofit3 = False
    get_amount = 0


    tickers = tickerscoin
    tickers2 = tickers2coin
    

    tick = tickers[symbol]
    tick2 = tickers2[symbol]

    exchange.dapiPrivate_post_leverage({"symbol": tick2, "leverage": leverage})    
    inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, tick2,tick)
    count = 1
    

    while inPosition == False or ((longPosition == False and side ==1) or (shortPosition == False and side == -1)):
      # LOAD BARS
      bars = exchange.fetch_ohlcv(tick2, timeframe=t, since=None, limit=30)
      df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

      # BULL EVENT
      if longPosition == False and side == 1:
        exchange.cancel_all_orders(tick2)
        if shortPosition:
          self.logger.info("EXIT SHORT POSITION...")
          amount = position_info["positionAmt"][len(position_info.index) - 1]
          self.logger.info(f"Amount Short Exit Position: {amount}")
          self.shortExit(exchange,tick2, amount)
          inPosition = False
          shortPosition = False

        get_amount = self.get_max_position_available(exchange, tick, tick2, leverage, ProcessingMoney)
        self.logger.info(f"ENTERING LONG POSITION WITH: {get_amount}")
        l = self.longEnter(exchange,tick2, get_amount)
        takeprofit1 = False
        takeprofit2 = False
        takeprofit3 = False
        if l == False:
          break
        if l:
          longPosition = True
        message = "LONG ENTER\n" + "Total Money: " + balance
        content = f"Subject: {tick}\n{message}"
        self.logger.info(content)
        self.logger.info("============================")

      inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, tick2,tick)
      
      
      if longPosition:
        # STOP LOSS FOR LONG POSITION
        self.logger.info("SETTING STOPLOSS FOR LONG POSITION")
        get_amount = float(
            position_info["positionAmt"][len(position_info.index) - 1])
        # longExit(get_amount)
        entryprice = float(
            position_info["entryPrice"][len(position_info.index) - 1])
        entrylow = float(
            position_info["entryPrice"][len(position_info.index) - 1]) / 100
        self.logger.info(f"entryprice: {entryprice}")
        self.logger.info(f"entry - price: {entrylow}")
        # float(entryprice - (entrylow * stopLoss))
        stop = entryprice / (1+stopLoss/100)
        self.logger.info(f"stoploss: {stop}")
        self.stoplossLong(exchange,tick2, stop, get_amount)
        message = f"LONG EXIT (STOP LOSS): {get_amount}\n" + "Total Money: " + balance
        content = f"Subject: {tick}\n{message}"
        self.logger.info(content)
        self.logger.info(position_info)
        self.logger.info("============================")
        
        get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) / 3

        if takeprofit1 == False:
          # TAKE PROFIT FOR LONG POSITION
          # TAKE PROFIT 1
          self.logger.info("TAKE PROFIT 1")
          takep1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])
          self.takeProfitLong1(exchange,tick2, get_amount, takep1)
          takeprofit1 = True
          message = f"LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
              "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        if takeprofit2 == False:

          # TAKE PROFIT 2
          self.logger.info("TAKE PROFIT 2")
          takep2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
          self.takeProfitLong2(exchange,tick2, get_amount, takep2)
          takeprofit2 = True
          message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        if takeprofit3 == False:

          # TAKE PROFIT 3
          self.logger.info("TAKE PROFIT 3")
          takep3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3 + float(position_info["entryPrice"][len(position_info.index) - 1])
          takeprofit3= self.trailing_market(exchange,tick2, get_amount, takep3, 'sell')
          message = f"LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
                "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

      # BEAR EVENT
      elif shortPosition == False and side == -1:
        exchange.cancel_all_orders(tick2)
        if longPosition:
          self.logger.info("EXIT LONG POSITION...")
          amount = float(position_info["positionAmt"]
                          [len(position_info.index) - 1])
          self.logger.info(f"Amount Long Exit Position: {amount}")
          self.longExit(exchange,tick2, amount)
          inPosition = False
          longPosition = False

          get_amount = self.get_max_position_available(exchange, tick,tick2,leverage,ProcessingMoney)
          self.logger.info(f"ENTERING SHORT POSITION...: {get_amount}")
          s = self.shortEnter(exchange,tick2, get_amount)
          takeprofit1 = False
          takeprofit2 = False
          takeprofit3 = False
          if s == False:
            break
          if s:
            shortPosition = True
          message = "LONG ENTER\n" + "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          position_info = pd.DataFrame(current_positions, columns=[
                                        "symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
          self.logger.info(position_info)
          self.logger.info("============================")
          
      inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, tick2,tick)
      
      sleep(0.3)
      if shortPosition:
        # STOP LOSS FOR SHORT POSITION
        self.logger.info("SETTING STOPLOSS FOR SHORT POSITION")
        get_amount = float(
            position_info["positionAmt"][len(position_info.index) - 1]) * -1
        # shortExit(get_amount)
        stop = ((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * float(
            stopLoss)) + float(position_info["entryPrice"][len(position_info.index) - 1])
        self.logger.info(f"STOPLOSS Short: {stop}")
        self.stoplossShort(exchange,tick2, stop, get_amount)
        message = "LONG EXIT (STOP LOSS)\n" + "Total Money: " + balance
        content = f"Subject: {tick}\n{message}"
        self.logger.info(content)
        self.logger.info(position_info)
        self.logger.info("============================")

        get_amount = (float(position_info["positionAmt"][len(position_info.index) - 1]) / 3) * -1
        # TAKE PROFIT FOR SHORT POSITION
        # TAKE PROFIT 1
        if takeprofit1 == False:
          self.logger.info("TAKE PROFIT 1")
          takeps1 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
              float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1
          takeprofit1 = self.takeProfitShort1(exchange,tick2, get_amount, takeps1)
          message = f"LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
              "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")


        # TAKE PROFIT 2
        if takeprofit2 == False:
          self.logger.info("TAKE PROFIT 2")
          takeps2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
              float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
          takeprofit2 = self.takeProfitShort2(exchange,tick2, get_amount, takeps2)
          message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
              "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        # TAKE PROFIT 3
        if takeprofit3 == False:
          self.logger.info("TAKE PROFIT 3")
          takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp3
          takeprofit3 = self.trailing_market(exchange,tick2, get_amount, takeps3, 'buy')
          message = f"LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
              "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

      if inPosition == False:
        self.logger.info("NO POSITION YET...")
        self.logger.info("============================")
      
      count +=1

      if count == 3:
        break
      
      inPosition, longPosition, shortPosition,balance, free_balance, current_positions,position_info = self.in_position_check(exchange, tick2, tick)

      if shortPosition:
        stop_price = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])
        tkp1 =float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1
        tkp2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
        tk1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1
        tk2=float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2
        tk3 =float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3
        self.logger.info(f"IN A SHORT POSITION WITH:")
        self.logger.info(f"STOP LOSS PRICE: {stop_price}")
        self.logger.info(f"TAKE PROFIT 1 PRICE: {tkp1}")
        self.logger.info(f"TAKE PROFIT 2 PRICE: {tkp2}")
        self.logger.info(f"TAKEPROFIT 1 is - {tk1}")
        self.logger.info(f"TAKEPROFIT 2 is - {tk2}")
        self.logger.info(f"TAKEPROFIT 3 is - {tk3}")

      elif longPosition:
        self.logger.info("IN A LONG POSITION WITH: ")
        self.logger.info("PRICE: {}", float(df["close"][len(df.index)-1]))
        self.logger.info("STOP LOSS PRICE: {} ", (float(position_info["entryPrice"][len(position_info.index) - 1])- (float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss))
        self.logger.info("TAKE PROFIT 1 PRICE: {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])))
        self.logger.info("TAKE PROFIT 2 PRICE:{}",  (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])))
        self.logger.info("TAKEPROFIT 1 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1))
        self.logger.info("TAKEPROFIT 2 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2))
        self.logger.info("TAKEPROFIT 3 is + {}", (float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3))
  
  
  # LONG ENTER
  def longEnter(self, exchange, symbol, get_amount):
    try:
      order = exchange.create_market_buy_order(symbol, get_amount)
      self.logger.info(order)
      self.trade_info.append({'id': order['id'], 'symbol': symbol, 'side': 'buy', 'entry_price': order['price']})
    except InsufficientFunds as e :
      self.logger.error("there is not enought funding to make the trade ! - {}".format(e))
      return False
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True

  # LONG EXIT
  def longExit(self, exchange,symbol, amount):
    try:
      order = exchange.create_market_sell_order(symbol, amount, {"reduceOnly": True})
      self.logger.info(order)

    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True


  # SHORT ENTER
  def shortEnter(self, exchange,symbol, get_amount):
    try:
      order = exchange.create_market_sell_order(symbol, get_amount)
      self.logger.info(order)
      self.trade_info.append({'id': order['id'], 'symbol': symbol, 'side': 'sell', 'entry_price': order['price']})
    except InsufficientFunds as e :
      self.logger.error("there is not enought funding to make the trade ! - {}".format(e))
      return False
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True

  # SHORT EXIT
  def shortExit(self, exchange,symbol, amount):
    try:
      order = exchange.create_market_buy_order(symbol, amount, {"reduceOnly": True})
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False

      
    return True
  # TAKEPROFIT LONG #1


  def takeProfitLong1(self, exchange,symbol, get_amount, takep1):
    side = 'sell'
    order_type_tk = 'TAKE_PROFIT'
    params = {'triggerPrice': takep1, 'stopPrice': takep1, 'reduceOnly': True}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takep1}")

    try:
      order = exchange.createOrder(
          symbol, order_type_tk, side, get_amount, takep1 ,params=params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True 

  # TAKEPROFIT LONG #2


  def takeProfitLong2(self, exchange,symbol, get_amount, takep2):
    side = 'sell'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice': takep2, 'reduceOnly': True, 'stopPrice':takep2}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takep2}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takep2,params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True 

  # TAKEPROFIT LONG #3

  def takeProfitLong3(self, exchange,symbol, get_amount, takep3):
    side = 'sell'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice': takep3, 'reduceOnly': True, 'stopPrice':takep3}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takep3}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takep3,params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True
  
  # STOPLOSS LONG

  def stoplossLong(self, exchange,symbol, stop,  get_amount):
    order_type_sl = 'STOP_MARKET'
    side = 'sell'
    params = {'stopPrice': stop, 'closePosition': True}
    self.logger.info(f"quantity:{get_amount}")

    try:
      order = exchange.createOrder(symbol, order_type_sl, side, get_amount,None, params=params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      self.logger.error("error: stoploss")
      return False
    
    return True
  
  # TAKEPROFIT SHORT #1

  def takeProfitShort1(self, exchange,symbol, get_amount, takeps1):
    side = 'buy'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice': takeps1,'reduceOnly': True, 'stopPrice': takeps1}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takeps1}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takeps1, params=params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True
  
  # TAKEPROFIT SHORT #2

  def takeProfitShort2(self, exchange,symbol, get_amount, takeps2):
    side = 'buy'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice':takeps2, 'reduceOnly': True, 'stopPrice': takeps2}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takeps2}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takeps2, params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True


  # TAKEPROFIT SHORT #3

  def takeProfitShort3(self, exchange,symbol, get_amount, takeps3):
    side = 'buy'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice':takeps3, 'reduceOnly': True, 'stopPrice': takeps3 }
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takeps3}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takeps3, params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured - {}".format(e))
      return False
    
    return True

  # STOPLOSS SHORT

  def stoplossShort(self, exchange,symbol, stop, get_amount):
    order_type_sl = 'STOP_MARKET'
    side = 'buy'
    params = {'stopPrice': stop, 'closePosition': True}
    self.logger.info(f"quantity:{get_amount}")

    try:
      order = exchange.createOrder(symbol, order_type_sl, side, None, params=params)
      self.logger.info(order)

    except Exception as e:
      self.logger.error("an exception occured stoplossShort - {}".format(e))
      return False
    
    return True
    
  # stoploss_market
  def trailing_market(self, exchange, symbol, get_amount, takeps3, side):
    side = side
    order_type = 'TRAILING_STOP_MARKET'
    rate = '0.2'
    price = None
    params = {
        'activationPrice': takeps3,
        'callbackRate': rate,
        'reduceOnly': True,
    }
    self.logger.info(f"the activantion price is : {takeps3}")
    self.logger.info("#########################################")
    try:
      order = exchange.create_order(symbol, order_type, side, get_amount, price, params)
      self.logger.info(order)
    except Exception as e:
      self.logger.error("an exception occured in trailing_market - {}".format(e))
      if side =="sell":
        self.takeProfitLong3(exchange, symbol, get_amount, takeps3)
      else:
        self.takeProfitShort3(exchange, symbol, get_amount, takeps3)
      return True
    
    return True
    
  def get_max_position_available(self, exchange, tick, symbol, leverage, ProcessMoney):
    to_use = float(exchange.fetch_balance().get(tick).get('free')/0.000026)
    price = float(exchange.fetchTicker(symbol).get('last'))
    decide_position_to_use = (((to_use/100)*ProcessMoney)*leverage) / price
    return decide_position_to_use
    #float(((free_balance["USDT"] / 100) * ProcessingMoney) * leverage) / (df["close"][len(df.index) - 1])

  def in_position_check(self, exchange: ccxt.binance, symbol, tick:None):
    
    longPosition = False
    shortPosition = False
    inPosition = False
    balance = exchange.fetch_balance()
    # self.logger.info(f"exchange:{exchange.alias} ", balance)
    free_balance = exchange.fetchFreeBalance()
    positions = balance['info']['positions']
    current_positions = [position for position in positions if float(
        position['positionAmt']) != 0 and position['symbol'] == symbol]
    self.logger.info(f"Current position: {current_positions}")
    self.logger.info("============================")
    position_info = pd.DataFrame(current_positions, columns=[
                                  "symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])

    # Check if it is in position
    if not position_info.empty and float(position_info["positionAmt"][len(position_info.index) - 1]) != 0:
      inPosition = True
      self.logger.info(f"already in position {position_info['positionSide'][len(position_info.index) - 1]}")
    if inPosition and float(position_info["positionAmt"][len(position_info.index) - 1]) > 0:
      longPosition = True
      shortPosition = False
      self.logger.info(f"already in  a LONG= {longPosition} position symbol {symbol}")
      self.logger.info("============================")
    elif inPosition and float(position_info["positionAmt"][len(position_info.index) - 1]) < 0 :
      shortPosition = True
      longPosition = False
      self.logger.info(f"already in  a SHORT={shortPosition}  position symbol {symbol}")
      self.logger.info("============================")

    else:
      self.logger.info("not in position right now")
      inPosition = False
    if tick != None:
      try:
        balance = str(balance['total'][tick])
      except Exception as e:
        self.logger.error("an exception occured in_position_check - {}".format(e))

    return inPosition,longPosition, shortPosition, balance, free_balance, current_positions, position_info 

  def update_profit_thread(self):
    while True:
        for symbol in self.profit_loss:
            self.update_profit(symbol)
          
        sleep(180)

  def update_profit(self, symbol):
    for ex in self.ex:
      # Get the list of closed orders for the given symbol
      closed_orders = ex.fetch_closed_orders(symbol=symbol)

      # Loop through the closed orders and update the profit and loss
      for order in closed_orders:
        
        # Check if the order has been closed
        if order['status'] == 'closed':
          
          # Get the order information
          symbol = order['symbol']
          side = order['side']
          entry_price = order['price']
          exit_price = order['average']
          quantity = order['amount']
          filled_quantity = order['filled']
          fees = order['fees']['cost']
          order_id = order['id']
          
          # Calculate the profit/loss
          if side == 'buy':
            pnl = (exit_price - entry_price) * filled_quantity - fees
          else:
            pnl = (entry_price - exit_price) * filled_quantity - fees
            
          # Update the trade information in the trade_info list
          for trade in self.trade_info:
            if trade['id'] == order_id:
              trade['exit_price'] = exit_price
              trade['profit_loss'] = pnl
              
              # Write the trade information to the CSV file
              with open("data/pnl/all_trades.csv", mode='a', newline='') as csv_file:
                  fieldnames = ['id', 'symbol', 'side', 'entry_price', 'exit_price', 'profit_loss']
                  writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                  writer.writerow(trade)
                  
              # Update the total profit/loss for the given symbol
              if symbol in self.profit_loss:
                self.profit_loss[symbol] += pnl
              else:
                self.profit_loss[symbol] = pnl
                
              # Remove the trade from the trade_info list if it is closed
              if filled_quantity == quantity:
                  self.trade_info.remove(trade)