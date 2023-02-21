import pathlib
from datetime import datetime
from os import path
from time import sleep

import pandas as pd
from ccxt import binancecoinm

from model.trades.trades import Trades
from tickets import tickers2coin, tickerscoin
from utils.util import (get_max_position_available, in_position_check,
                        start_thread)


class BinanceFuturesCoinm:
    def __init__(self, exchange:binancecoinm, symbol:str, side:int, t:int, leverage:int,tp1:float,tp2:float, tp3:float,stopLoss:float,ProcessingMoney:float, logger):
        self.takeprofit1:bool = False
        self.takeprofit2:bool = False
        self.takeprofit3:bool = False
        self.get_amount:float = 0
        self.thread = None
        self.trade_info = []
        self.profit_loss = {}
        self.logger = logger
        self.trades = Trades(self.logger)
        
        self.trading(exchange, symbol, side, t, leverage,tp1,tp2, tp3,stopLoss,ProcessingMoney)
        start_thread(exchange, self.thread, self.profit_loss, self.trade_info, self.thread, self.logger)

    def trading(self, exchange:binancecoinm, symbol:str, side:int, t:str, leverage:int,tp1:float,tp2:float, tp3:float,stopLoss:float,ProcessingMoney:float):
        tickers:dict[str,str] = tickerscoin
        tickers2: dict[str,str] = tickers2coin
        

        tick:str = tickers[symbol]
        tick2:str = tickers2[symbol]

        exchange.dapiPrivate_post_leverage({"symbol": tick2, "leverage": leverage})    
        inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, tick2,tick)
        count:int = 1
        

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
                    self.trades.shortExit(exchange,tick2, amount)
                    inPosition = False
                    shortPosition = False

                get_amount = get_max_position_available(exchange, tick, tick2, leverage, ProcessingMoney)
                self.logger.info(f"ENTERING LONG POSITION WITH: {get_amount}")
                l = self.trades.longEnter(exchange,tick2, get_amount, self.trade_info)
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

            inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, tick2,tick)
            
            
            if longPosition:
                # STOP LOSS FOR LONG POSITION
                self.logger.info("SETTING STOPLOSS FOR LONG POSITION")
                get_amount = float(position_info["positionAmt"][len(position_info.index) - 1])
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
                self.trades.stoplossLong(exchange,tick2, stop, get_amount)
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
                    takeprofit1 = self.trades.takeProfitLong1(exchange,tick2, get_amount, takep1)
                    message = f"LONG EXIT (TAKE PROFIT 1): {get_amount}\n" + \
                        "Total Money: " + balance
                    content = f"Subject: {tick}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                if takeprofit2 == False:

                    # TAKE PROFIT 2
                    self.logger.info("TAKE PROFIT 2")
                    takep2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
                    takeprofit2 = self.trades.takeProfitLong2(exchange,tick2, get_amount, takep2)
                    message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                            "Total Money: " + balance
                    content = f"Subject: {tick}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                if takeprofit3 == False:

                    # TAKE PROFIT 3
                    self.logger.info("TAKE PROFIT 3")
                    takep3 = ((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * tp3) + float(position_info["entryPrice"][len(position_info.index) - 1])
                    takeprofit3 = self.trades.trailing_market(exchange,tick2, get_amount, takep3, 'sell')
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
                    self.trades.longExit(exchange,tick2, amount)
                    inPosition = False
                    longPosition = False

                    get_amount = get_max_position_available(exchange, tick,tick2,leverage,ProcessingMoney)
                    self.logger.info(f"ENTERING SHORT POSITION...: {get_amount}")
                    s = self.trades.shortEnter(exchange,tick2, get_amount, self.trade_info)
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
                
            inPosition,longPosition, shortPosition, balance, free_balance, current_positions,position_info = in_position_check(exchange, tick2,tick)
            
            if shortPosition:
                # STOP LOSS FOR SHORT POSITION
                self.logger.info("SETTING STOPLOSS FOR SHORT POSITION")
                get_amount = float(position_info["positionAmt"][len(position_info.index) - 1]) * -1
                # shortExit(get_amount)
                stop = ((float(position_info["entryPrice"][len(position_info.index) - 1]) / 100) * float(
                    stopLoss)) + float(position_info["entryPrice"][len(position_info.index) - 1])
                self.logger.info(f"STOPLOSS Short: {stop}")
                self.trades.stoplossShort(exchange,tick2, stop, get_amount)
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
                    takeprofit1 = self.trades.takeProfitShort1(exchange,tick2, get_amount, takeps1)
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
                    takeprofit2 = self.trades.takeProfitShort2(exchange,tick2, get_amount, takeps2)
                    message = f"LONG EXIT (TAKE PROFIT 2): {get_amount}\n" + \
                        "Total Money: " + balance
                    content = f"Subject: {tick}\n{message}"
                    self.logger.info(content)
                    self.logger.info("============================")

                # TAKE PROFIT 3
                if takeprofit3 == False:
                    self.logger.info("TAKE PROFIT 3")
                    takeps3 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp3
                    takeprofit3 = self.trades.trailing_market(exchange,tick2, get_amount, takeps3, 'buy')
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
            
            inPosition, longPosition, shortPosition,balance, free_balance, current_positions,position_info = in_position_check(exchange, tick2, tick)
            
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
                stop_price = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * stopLoss + float(position_info["entryPrice"][len(position_info.index) - 1])
                tkp1 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp1
                tkp2 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp2
                tkp3 = float(position_info["entryPrice"][len(position_info.index) - 1])-(float(position_info["entryPrice"][len(position_info.index) - 1])/100) * tp3
                tk1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1
                tk2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2
                tk3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3
                
                self.logger.info(f"IN A SHORT POSITION WITH:")
                self.logger.info(f"STOP LOSS PRICE: {stop_price}")
                self.logger.info(f"TAKE PROFIT 1 PRICE: {tkp1}")
                self.logger.info(f"TAKE PROFIT 2 PRICE: {tkp2}")
                self.logger.info(f"TAKE PROFIT 3 PRICE: {tkp3}")
                self.logger.info(f"TAKEPROFIT 1 is - {tk1}")
                self.logger.info(f"TAKEPROFIT 2 is - {tk2}")
                self.logger.info(f"TAKEPROFIT 3 is - {tk3}")

            elif longPosition:
                stop_price = round(float(position_info["entryPrice"][len(position_info.index) - 1])- (float(position_info["entryPrice"][len(position_info.index) - 1])/100) * stopLoss)
                tkp1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1 + float(position_info["entryPrice"][len(position_info.index) - 1])
                tkp2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2 + float(position_info["entryPrice"][len(position_info.index) - 1])
                tkp3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3 + float(position_info["entryPrice"][len(position_info.index) - 1])
                tk1 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp1
                tk2 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp2
                tk3 = float(position_info["entryPrice"][len(position_info.index) - 1]) / 100 * tp3
                
                self.logger.info("IN A LONG POSITION WITH: ")
                self.logger.info("PRICE: {} ", df["close"][len(df.index)-1])
                self.logger.info(f"STOP LOSS PRICE: {stop_price} ")
                self.logger.info(f"TAKE PROFIT 1 PRICE: {tkp1}")
                self.logger.info(f"TAKE PROFIT 2 PRICE:{tkp2}")
                self.logger.info(f"TAKE PROFIT 3 PRICE:{tkp3}")
                self.logger.info(f"TAKEPROFIT 1 is + {tk1}" )
                self.logger.info(f"TAKEPROFIT 2 is + {tk2}")
                self.logger.info(f"TAKEPROFIT 3 is + {tk3}")
        
        