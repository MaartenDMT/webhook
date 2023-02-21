import pathlib
from datetime import datetime
from os import path
from time import sleep

import pandas as pd
from ccxt import binance

from model.trades.trades import Trades
from utils.util import in_position_check, start_thread


class BinanceFuturesUsdtm:
    def __init__(self, exchange, symbol, side, t, leverage,tp1,tp2, tp3,stopLoss,ProcessingMoney, logger):
        self.takeprofit1:bool = False
        self.takeprofit2:bool = False
        self.takeprofit3:bool = False
        self.get_amount:float = 0
        self.logger = logger
        self.thread = None
        self.trade_info = []
        self.profit_loss = {}
        self.trades = Trades(self.logger)
        
        self.logger.info("USDTM LOGGER ACTIVE")
        self.trading(exchange, symbol, side, t, leverage,tp1,tp2, tp3,stopLoss,ProcessingMoney)
        start_thread(exchange, symbol, self.profit_loss, self.trade_info, self.thread, self.logger)
        
    def trading(self, exchange:binance, symbol:str, side:int, t:str, leverage:int,tp1:float,tp2:float, tp3:float,stopLoss:float,ProcessingMoney:float):
        self.logger.info(f"exchange: {exchange.name} ")
        
        inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, symbol,None, self.logger)
        count:int=1

        if inPosition == False:
            exchange.fapiPrivate_post_leverage({"symbol": symbol, "leverage": leverage, })
        if symbol in ["WAVESUSDT"]:
            exchange.fapiPrivate_post_leverage({"symbol": symbol, "leverage": 8, })

        while inPosition == False or ((longPosition == False and side ==1) or (shortPosition == False and side == -1)):
            
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
                    self.trades.shortExit(exchange,symbol, amount)
                    inPosition = False
                    shortPosition = False

                    self.get_amount_l = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
                    self.logger.info(f"usdtm - ENTERING LONG POSITION WITH: {self.get_amount_l}")

                    l = self.trades.longEnter(exchange,symbol,self.get_amount_l, self.trade_info)
                    takeprofit1 = False
                    takeprofit2 = False
                    takeprofit3 = False
                    
                if l == False:
                    break
                if l:
                    longPosition = True
                    message = "usdtm - LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, symbol, None, self.logger)
                
                if longPosition:
                    # STOP LOSS FOR LONG POSITION
                    self.logger.info("usdtm -SETTING STOPLOSS FOR LONG POSITION")
                    get_amount = self.get_amount_l
                    #longExit(get_amount)
                    entryprice = float(position_info["entryPrice"])
                    entrylow = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100
                    self.logger.info(f"usdtm - entryprice: {entryprice}")
                    self.logger.info(f"usdtm - entry - price: {entrylow}")
                    stop = entryprice / (1+stopLoss/100) #float(entryprice - (entrylow * stopLoss))
                    self.logger.info(f"usdtm - stoploss: {stop}")
                    self.trades.stoplossLong(exchange,symbol, stop, get_amount)
                    message = f"usdtm - LONG EXIT (STOP LOSS): {get_amount}\n" + "Total Money: " + \
                        str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info(position_info)
                    self.logger.info("============================")
                    
                    get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])/ 3

                if takeprofit1 == False:
                    # TAKE PROFIT FOR LONG POSITION
                    # TAKE PROFIT 1
                    self.logger.info("usdtm - TAKE PROFIT 1")
                    takep1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100* tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])
                    takeprofit1 = self.trades.takeProfitLong1(exchange,symbol, get_amount, takep1)
                    message = f"usdtm - LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")


                if takeprofit2 == False:

                    # TAKE PROFIT 2
                    self.logger.info("usdtm - TAKE PROFIT 2")
                    takep2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
                    takeprofit2 = self.trades.takeProfitLong2(exchange,symbol, get_amount, takep2)
                    message = f"usdtm -LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                if takeprofit3 == False:

                    # TAKE PROFIT 3
                    self.logger.info("usdtm - TAKE PROFIT 3")
                    takep3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3 + float(position_info["entryPrice"][len(position_info.index) - 1])
                    takeprofit3 = self.trades.trailing_market(exchange,symbol, get_amount, takep3, 'sell')
                    message = f"usdtm - LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")


            # BEAR EVENT
            elif shortPosition == False and side == -1:
                exchange.cancel_all_orders(symbol)
                if longPosition:
                    self.logger.info("usdtm - EXIT LONG POSITION...")
                    amount = float(position_info["positionAmt"][len(position_info.index) - 1])
                    self.logger.info(f"Amount Long Exit Position: {amount}")
                    self.trades.longExit(exchange,symbol, amount)
                    inPosition = False
                    longPosition = False

                self.get_amount_s = float(free_balance["USDT"]) / 100 * ProcessingMoney * leverage / float(df["close"][len(df.index) - 1])
                self.logger.info(f"usdtm - ENTERING SHORT POSITION...: {self.get_amount_s}")
                s = self.trades.shortEnter(exchange,symbol, self.get_amount_s, self.trade_info)
                takeprofit1 = False
                takeprofit2 = False
                takeprofit3 = False
                if s == False:
                    break
                if s:
                    shortPosition = True
                message = "usdtm - LONG ENTER\n" + "Total Money: " + str(balance['total']["USDT"])
                content = f"Subject: {symbol}\n{message}"
                self.logger.info(content)
                position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
                self.logger.info(position_info)
                self.logger.info("============================")

            inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, symbol, None, self.logger)
            
            if shortPosition:
                # STOP LOSS FOR SHORT POSITION
                self.logger.info("usdtm - SETTING STOPLOSS FOR SHORT POSITION")
                get_amount = self.get_amount_s
                #shortExit(get_amount)
                stop = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])
                self.logger.info(f"usdtm - STOPLOSS Short: {stop}")
                self.trades.stoplossShort(exchange,symbol, stop, get_amount)
                message = "usdtm - LONG EXIT (STOP LOSS)\n" + "Total Money: " + \
                    str(balance['total']["USDT"])
                content = f"Subject: {symbol}\n{message}"
                self.logger.info(content)
                self.logger.info(position_info)
                self.logger.info("============================")

                get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) / (3 *-1)
                # TAKE PROFIT FOR SHORT POSITION
                # TAKE PROFIT 1
                if takeprofit1 == False:
                    self.logger.info("usdtm - TAKE PROFIT 1")
                    takeps1 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp1
                    takeprofit1 = self.trades.takeProfitShort1(exchange,symbol, get_amount, takeps1)
                    message = f"usdtm - LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")



                # TAKE PROFIT 2
                if takeprofit2 == False:
                    self.logger.info("usdtm - TAKE PROFIT 2")
                    takeps2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(
                        float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
                    takeprofit2 =self.trades.takeProfitShort2(exchange,symbol, get_amount, takeps2)
                    message = f"usdtm - LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                # TAKE PROFIT 3
                if takeprofit3 == False:
                    self.logger.info("usdtm - TAKE PROFIT 3")
                    takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1]) - float(position_info["entryPrice"][len(position_info.index) - 1])/100 * tp3
                    takeprofit3 = self.trades.trailing_market(exchange,symbol, get_amount, takeps3, 'buy')
                    message = f"usdtm - LONG EXIT (TAKE PROFIT 3): {get_amount}\n" + \
                        "Total Money: " + str(balance['total']["USDT"])
                    content = f"Subject: {symbol}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

            if inPosition == False:
                self.logger.info("NO POSITION YET...")
                self.logger.info("============================")
                
            count +=1

            
            if count == 3:
                break 
            
            inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, symbol, None, self.logger)

            # Write the trade information to the CSV file
            # Convert trade_info to a DataFrame
            df = pd.DataFrame(self.trade_info)

            # Write the DataFrame to a CSV file
            file = f'data/trades/{exchange}'
            time_stamp = datetime.now()  # - dt.timedelta(hours=6)
            time_stamp = time_stamp.strftime('%Y-%m-%d')
            if path.exists(file):
                df.to_csv(f'{file}/{time_stamp}.csv', index=False)
            else:
                self.logger.error("coudln't make path, making path")
                pathlib.Path(file).mkdir(parents=True, exist_ok=True)
                sleep(0.5)
                df.to_csv(f'{file}/{time_stamp}.csv', index=False)
            
            if shortPosition:
                stop_price = round(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1]),2)
                tk1 = round(float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1,2)
                tk2 = round(float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2,2)
                tk3 = round(float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp3,2)
                tkp1 = round(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1,2)
                tkp2 = round(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2,2)
                tkp3 = round(float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3,2)
                
                self.logger.info("usdtm - IN A SHORT POSITION WITH:")
                self.logger.info(f"usdtm - STOP LOSS PRICE: {stop_price}")
                self.logger.info(f"usdtm - TAKE PROFIT 1 PRICE: {tk1}" )
                self.logger.info(f"usdtm - TAKE PROFIT 2 PRICE: {tk2}" )
                self.logger.info(f"usdtm - TAKE PROFIT 3 PRICE: {tk3}" )
                self.logger.info(f"usdtm - TAKEPROFIT 1 is - {tkp1}")
                self.logger.info(f"usdtm - TAKEPROFIT 2 is - {tkp2}")
                self.logger.info(f"usdtm - TAKEPROFIT 3 is - {tkp3}")


            elif longPosition:
                price = round(float(df["close"][len(df.index)-1]),2)
                stop_price =round(float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss,2)
                tk1 =round(((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp1) + float(position_info["entryPrice"][len(position_info.index) - 1]),2)
                tk2 =round(((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp2) + float(position_info["entryPrice"][len(position_info.index) - 1]),2)
                tk3 =round(((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp3) + float(position_info["entryPrice"][len(position_info.index) - 1]),2)
                tkp1 =round((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp1,2)
                tkp2 =round((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp2,2)
                tkp3 =round((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp3,2)
                
                self.logger.info("usdtm - IN A LONG POSITION WITH: ")
                self.logger.info(f"usdtm - PRICE: {price}")
                self.logger.info(f"usdtm - STOP LOSS PRICE: {stop_price}" )
                self.logger.info(f"usdtm - TAKE PROFIT 1 PRICE: {tk1}" )
                self.logger.info(f"usdtm - TAKE PROFIT 2 PRICE: {tk2}" )
                self.logger.info(f"usdtm - TAKE PROFIT 3 PRICE: {tk3}" )
                self.logger.info(f"usdtm - TAKEPROFIT 1 is + {tkp1}" )
                self.logger.info(f"usdtm - TAKEPROFIT 2 is + {tkp2}" )
                self.logger.info(f"usdtm - TAKEPROFIT 3 is + {tkp3}" )