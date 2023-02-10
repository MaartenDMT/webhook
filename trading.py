from concurrent.futures import ThreadPoolExecutor

import ccxt
import pandas as pd

# import tickets as ticks
import csv


class TradeCrypto:
  def __init__(self, request, ex, logger) -> str:
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
    
    self.trade()
    self.return_code = "Succeeded"
  
  def __str__(self) -> str:
    return self.return_code
    
    
  def trade(self):
    with ThreadPoolExecutor() as executor:
      executor.submit(self.execute_usdtm_trade, self.ex[0], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)
      executor.submit(self.execute_coinm_trade, self.ex[1], self.symbol, self.side, self.t, self.leverage, self.tp1, self.tp2, self.tp3, self.stopLoss, self.ProcessingMoney)

  def execute_usdtm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    self.usdtm(exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)

  def execute_coinm_trade(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    
    #  ticker = ticks.tickers
    # ttick = ticker[symbol]
    # for d in tickers2:
    #     if d == ttick:
    #         self.logger.info(d)
    #         self.coinm(exchange, d, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)
    
    # read the symbols from the CSV file
    with open("coinm.csv") as file:
        reader = csv.reader(file)
        next(reader)  # skip the header row
        tickers2 = [row[0] for row in reader]
    
    # read the symbols from the CSV file
    with open("usdm.csv") as file:
        reader = csv.reader(file)
        next(reader)  # skip the header row
        ticker = [row[0] for row in reader]
        
    ttick = ticker[symbol]
    for d in tickers2:
        if d == ttick:
            self.logger.info(d)
            self.coinm(exchange, d, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney)


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
          self.logger.info("EXIT SHORT POSITION...")
          amount = float(position_info["positionAmt"][len(position_info.index) - 1])
          self.logger.info(f"Amount Short Exit Position: {amount}")

          self.shortExit(exchange,symbol, amount)

          inPosition = False
          shortPosition = False

        get_amount = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
        self.logger.info(f"ENTERING LONG POSITION WITH: {get_amount}")

        l = self.longEnter(exchange,symbol, get_amount)
        takeprofit1 = False
        takeprofit2 = False
        takeprofit3 = False
        
        if l:
          longPosition = True
        ticker = symbol
        message = "LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
        content = f"Subject: {ticker}\n{message}"
        self.logger.info(content)
        self.logger.info("============================")

        inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol, None)
        
        if longPosition:
          # STOP LOSS FOR LONG POSITION
          self.logger.info("SETTING STOPLOSS FOR LONG POSITION")
          get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])
          #longExit(get_amount)
          entryprice = float(position_info["entryPrice"])
          entrylow = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100
          self.logger.info(f"entryprice: {entryprice}")
          self.logger.info(f"entry - price: {entrylow}")
          stop = entryprice / (1+stopLoss/100) #float(entryprice - (entrylow * stopLoss))
          self.logger.info(f"stoploss: {stop}")
          self.stoplossLong(exchange,symbol, stop, get_amount)
          ticker = symbol
          message = f"LONG EXIT (STOP LOSS): {get_amount}\n" + "Total Money: " + \
              str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info(position_info)
          self.logger.info("============================")
          
          get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])/ 3

          if takeprofit1 == False:
            # TAKE PROFIT FOR LONG POSITION
            # TAKE PROFIT 1
            self.logger.info("TAKE PROFIT 1")

            takep1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100* tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])
            self.takeProfitLong1(exchange,symbol, get_amount, takep1)
            takeprofit1 = True
            ticker = symbol
            message = f"LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")


          if takeprofit2 == False:

            # TAKE PROFIT 2
            self.logger.info("TAKE PROFIT 2")
            takep2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
            self.takeProfitLong2(exchange,symbol, get_amount, takep2)
            takeprofit2 = True
            ticker = symbol
            message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")

          if takeprofit3 == False:

            # TAKE PROFIT 3
            self.logger.info("TAKE PROFIT 3")
            takep3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3 + float(position_info["entryPrice"][len(position_info.index) - 1])
            self.takeProfitLong3(exchange,symbol, get_amount, takep3)
            takeprofit3 = True
            ticker = symbol
            message = f"LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
                "Total Money: " + str(balance['total']["USDT"])
            content = f"Subject: {ticker}\n{message}"
            self.logger.info(content)
            self.logger.info("============================")


      # BEAR EVENT
      elif shortPosition == False and side == -1:
          exchange.cancel_all_orders(symbol)
          if longPosition:
            self.logger.info("EXIT LONG POSITION...")
            amount = float(position_info["positionAmt"][len(position_info.index) - 1])
            self.logger.info(f"Amount Long Exit Position: {amount}")
            self.longExit(exchange,symbol, amount)
            inPosition = False
            longPosition = False

          get_amount = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
          self.logger.info(f"ENTERING SHORT POSITION...: {get_amount}")
          s = self.shortEnter(exchange,symbol, get_amount)
          takeprofit1 = False
          takeprofit2 = False
          takeprofit3 = False
          if s:
            shortPosition = True
          ticker = symbol
          message = "LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
          self.logger.info(position_info)
          self.logger.info("============================")

      inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = self.in_position_check(exchange, symbol, None)
      
      if shortPosition:
        # STOP LOSS FOR SHORT POSITION
        self.logger.info("SETTING STOPLOSS FOR SHORT POSITION")
        get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) * -1
        #shortExit(get_amount)
        stop = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])
        self.logger.info(f"STOPLOSS Short: {stop}")
        self.stoplossShort(exchange,symbol, stop, get_amount)
        ticker = symbol
        message = "LONG EXIT (STOP LOSS)\n" + "Total Money: " + \
            str(balance['total']["USDT"])
        content = f"Subject: {ticker}\n{message}"
        self.logger.info(content)
        self.logger.info(position_info)
        self.logger.info("============================")

        get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) / (3 *-1)
        # TAKE PROFIT FOR SHORT POSITION
        # TAKE PROFIT 1
        if takeprofit1 == False:
          self.logger.info("TAKE PROFIT 1")
          
          takeps1 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp1
          self.takeProfitShort1(exchange,symbol, get_amount, takeps1)
          takeprofit1 = True
          ticker = symbol
          message = f"LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
              "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")



        # TAKE PROFIT 2
        if takeprofit2 == False:
          self.logger.info("TAKE PROFIT 2")
          takeps2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
              float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
          self.takeProfitShort2(exchange,symbol, get_amount, takeps2)
          takeprofit2 = True
          ticker = symbol
          message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
              "Total Money: " + str(balance['total']["USDT"])
          content = f"Subject: {ticker}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        # TAKE PROFIT 3
        if takeprofit3 == False:
          self.logger.info("TAKE PROFIT 3")
          takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp3
          self.takeProfitShort3(exchange,symbol, get_amount, takeps3)
          takeprofit3 = True
          ticker = symbol
          message = f"LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
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
        self.logger.info("IN A SHORT POSITION WITH:")
        self.logger.info("STOP LOSS PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKE PROFIT 1 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1)
        self.logger.info("TAKE PROFIT 2 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2)
        self.logger.info("TAKEPROFIT 1 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1)
        self.logger.info("TAKEPROFIT 2 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2)
        self.logger.info("TAKEPROFIT 3 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3)


      elif longPosition:
        self.logger.info("IN A LONG POSITION WITH: ")
        self.logger.info("PRICE: {}", float(df["close"][len(df.index)-1]))
        self.logger.info("STOP LOSS PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss)
        self.logger.info("TAKE PROFIT 1 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKE PROFIT 2 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKEPROFIT 1 is + {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1)
        self.logger.info("TAKEPROFIT 2 is + {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2)
        self.logger.info("TAKEPROFIT 3 is + {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3)

  #COIN- M
  def coinm(self, exchange, symbol, side, t, leverage, tp1, tp2, tp3, stopLoss, ProcessingMoney):
    self.logger.info(f"exchange: {exchange.name} ")
    takeprofit1 = False
    takeprofit2 = False
    takeprofit3 = False
    get_amount = 0

    tickers = ticks.tickerscoin
    tickers2 = ticks.tickers2coin
    

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
        l =self.longEnter(exchange,tick2, get_amount)
        takeprofit1 = False
        takeprofit2 = False
        takeprofit3 = False
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
          self.takeProfitLong3(exchange,tick2, get_amount, takep3)
          takeprofit3 = True
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
          self.takeProfitShort1(exchange,tick2, get_amount, takeps1)
          takeprofit1 = True
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
          self.takeProfitShort2(exchange,tick2, get_amount, takeps2)
          takeprofit2 = True
          message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
              "Total Money: " + balance
          content = f"Subject: {tick}\n{message}"
          self.logger.info(content)
          self.logger.info("============================")

        # TAKE PROFIT 3
        if takeprofit3 == False:
          self.logger.info("TAKE PROFIT 3")
          takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
              float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp3
          self.takeProfitShort3(exchange,tick2, get_amount, takeps3)
          takeprofit2 = True
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
        self.logger.info("IN A SHORT POSITION WITH:")
        self.logger.info("STOP LOSS PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKE PROFIT 1 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1)
        self.logger.info("TAKE PROFIT 2 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2)
        self.logger.info("TAKEPROFIT 1 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1)
        self.logger.info("TAKEPROFIT 2 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2)
        self.logger.info("TAKEPROFIT 3 is - {}",float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3)

      elif longPosition:
        self.logger.info("IN A LONG POSITION WITH: ")
        self.logger.info("PRICE: {}", float(df["close"][len(df.index)-1]))
        self.logger.info("STOP LOSS PRICE: {} ", float(position_info["entryPrice"][len(position_info.index) - 1])- (float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss)
        self.logger.info("TAKE PROFIT 1 PRICE: {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKE PROFIT 2 PRICE:{}",  float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1]))
        self.logger.info("TAKEPROFIT 1 is + {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1)
        self.logger.info("TAKEPROFIT 2 is + {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2)
        self.logger.info("TAKEPROFIT 3 is + {}", float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3)

  # LONG ENTER
  def longEnter(self, exchange, symbol, get_amount):
    try:
      order = exchange.create_market_buy_order(symbol, get_amount)
      self.logger.info(order)
    except Exception as e:
      self.logger.info("an exception occured - {}".format(e))
      return False


  # LONG EXIT
  def longExit(self, exchange,symbol, amount):
    try:
      order = exchange.create_market_sell_order(
          symbol, amount, {"reduceOnly": True})
      self.logger.info(order)
    except Exception as e:
      self.logger.info("an exception occured - {}".format(e))
      return False


  # SHORT ENTER
  def shortEnter(self, exchange,symbol, get_amount):
    try:
      order = exchange.create_market_sell_order(symbol, get_amount)
      self.logger.info(order)
    except Exception as e:
      self.logger.info("an exception occured - {}".format(e))
      return False


  # SHORT EXIT
  def shortExit(self, exchange,symbol, amount):
    try:
      order = exchange.create_market_buy_order(symbol, amount, {"reduceOnly": True})
      self.logger.info(order)
    except Exception as e:
      self.logger.info("an exception occured - {}".format(e))
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      return False


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
      self.logger.info("an exception occured - {}".format(e))
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      self.logger.info("error: stoploss")
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      return False


  # TAKEPROFIT SHORT #3

  def takeProfitShort3(self, exchange,symbol, get_amount, takeps3):
    side = 'buy'
    type_o = 'TAKE_PROFIT'
    params = {'triggerPrice':takeps3, 'reduceOnly': True, 'stopPrice': takeps3}
    self.logger.info(f"quantity:{get_amount}")
    self.logger.info(f"takeprofit :{takeps3}")

    try:
      order = exchange.create_order(symbol, type_o, side, get_amount, takeps3, params)
      self.logger.info(order)
    except Exception as e:
      self.logger.info("an exception occured - {}".format(e))
      return False

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
      self.logger.info("an exception occured - {}".format(e))
      return False

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
        self.logger.info("an exception occured - {}".format(e))

    return inPosition,longPosition, shortPosition, balance, free_balance, current_positions, position_info 


