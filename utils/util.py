from decimal import Decimal
import pathlib
import threading
from datetime import datetime
from os import path
from time import sleep
import ccxt

from tickets import tickers

import pandas as pd
from ccxt.base.errors import BadSymbol


def get_max_position_available(exchange, tick: str, symbol: str, leverage: int, ProcessMoney: float):
    to_use = float(exchange.fetch_balance().get(tick).get('free'))
    price = float(exchange.fetchTicker(symbol).get('last'))
    decide_position_to_use = (((to_use/100)*ProcessMoney)*leverage) / price
    print(f"the amount to be used: {decide_position_to_use}")
    
    return decide_position_to_use

def get_max_position_available_s(exchange, tick: str, symbol: str, leverage: int, ProcessMoney: float):
    
    to_use = float(exchange.fetch_balance().get(tick).get('free'))
    price = float(exchange.fetchTicker(symbol).get('last'))
    decide_position_to_use = ((((to_use/100)*ProcessMoney)*leverage) / price)
    adjust_amount_size = adjust_amount(exchange, symbol, decide_position_to_use)
    print(f"the amount to be used: {adjust_amount_size}")
    
    return decide_position_to_use

def adjust_amount(exchange: ccxt.binance, symbol:str, amount:float):
    symbol_data = exchange.load_markets()[transform_symbol(symbol)]
    lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', symbol_data['info']['filters']))
    step_size = Decimal(lot_size_filter['stepSize'])
    adjusted_amount = (Decimal(str(amount)) // step_size) * step_size
    print(adjusted_amount)
    return float(adjusted_amount)

def transform_symbol(symbol:str)->str:
    base_currency = symbol[:len(symbol) // 2]
    quote_currency = symbol[len(symbol) // 2:]
    transformed_symbol = f"{base_currency}/{quote_currency}"
    return transformed_symbol
    
def in_position_check_s(exchange, symbol: str, tick: None, logger):
    longPosition = False
    shortPosition = False
    inPosition = False
    ticker_balance = float(exchange.fetch_balance().get(tick).get('free'))
    usdt_balance = float(exchange.fetch_balance().get("USDT").get('free'))
    price = float(exchange.fetchTicker(symbol).get('last'))
    
    return usdt_balance, ticker_balance, price
    
def in_position_check(exchange, symbol: str, tick: None, logger):

    longPosition = False
    shortPosition = False
    inPosition = False
    balance = exchange.fetch_balance()
    # self.logger.info(f"exchange:{exchange.alias} ", balance)
    free_balance = exchange.fetchFreeBalance()
    positions = balance['info']['positions']
    current_positions = [position for position in positions if float(
        position['positionAmt']) != 0 and position['symbol'] == symbol]
    logger.info(f"Current position: {current_positions}")
    logger.info("============================")
    position_info = pd.DataFrame(current_positions, columns=[
        "symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])

    # Check if it is in position
    if not position_info.empty and float(position_info["positionAmt"][len(position_info.index) - 1]) != 0:
        inPosition = True
        logger.info(
            f"already in position {position_info['positionSide'][len(position_info.index) - 1]}")
    if inPosition and float(position_info["positionAmt"][len(position_info.index) - 1]) > 0:
        longPosition = True
        shortPosition = False
        logger.info(
            f"already in  a LONG= {longPosition} position symbol {symbol}")
        logger.info("============================")
    elif inPosition and float(position_info["positionAmt"][len(position_info.index) - 1]) < 0:
        shortPosition = True
        longPosition = False
        logger.info(
            f"already in  a SHORT={shortPosition}  position symbol {symbol}")
        logger.info("============================")

    else:
        logger.info("not in position right now")
        inPosition = False
    if tick != None:
        try:
            balance = str(balance['total'][tick])
        except Exception as e:
            logger.error(
                "an exception occured in_position_check - {}".format(e))

    return inPosition, longPosition, shortPosition, balance, free_balance, current_positions, position_info


def start_thread(exchange, symbol, profit_loss, trade_info, thread, logger) -> None:
    
    # check if the thread is already running
    if thread and thread.is_alive():
        logger.info("Thread is already running")
        return

    try:
        logger.info("starting thread !")
        thread = threading.Thread(target=update_profit_thread, args=(exchange, symbol, profit_loss,
                                  trade_info, logger), daemon=True)  # start a new thread if no thread is currently running
        thread.start()
        thread.join()
    except Exception as e:
        logger.error(e)
        


def update_profit_thread(exchange, symbol, profit_loss, trade_info, logger):
    update_profit(exchange, symbol, profit_loss, trade_info, logger)


def update_profit(exchange, symbol: str, profit_loss: dict, trade_info: list, logger):

    # Get the list of closed orders for the given symbol
    ex = exchange
    closed_orders = fetch_closed_orders(symbol, ex, logger)
    logger.info(
        f"starting to log the profit\loss for exchange: {ex} with symbol: {symbol}")

    if closed_orders == None:
        logger.info("there is no order closed history return to the main loop")
        return

    # Loop through the closed orders and update the profit and loss
    for order in closed_orders:

        # Check if the order has been closed
        if order['status'] == 'closed':

            # Get the order information
            symbol = symbol
            side = order['side']
            entry_price = order['price']
            exit_price = order['average']
            quantity = order['amount']
            filled_quantity = order['filled']
            order_id = order['id']

            # Calculate the profit/loss
            if side == 'buy':
                pnl = (exit_price - entry_price) * filled_quantity - \
                    ((filled_quantity/100)*0.02 + (filled_quantity/100)*0.04)
            else:
                pnl = (entry_price - exit_price) * filled_quantity - \
                    ((filled_quantity/100)*0.02 + (filled_quantity/100)*0.04)

            # Read the trade information from the CSV file into a DataFrame
            # file = f'data/trades/{exchange}'
            time_stamp = datetime.now()  # - dt.timedelta(hours=6)
            time_stamp = time_stamp.strftime('%Y-%m-%d')
            trade_df = None
            try:
                trade_df = pd.DataFrame(trade_info)  
            except Exception as e:
                logger.error("there is no data -", e)
                break

            # Loop through the trades in the DataFrame
            for index, trade in trade_df.iterrows():
                if trade['id'] == order_id:
                    logger.info("reading the csv trades files")
                    trade['exit_price'] = exit_price
                    trade['profit_loss'] = pnl

                    # Write the trade information to the CSV file
                    fieldnames = ['exchange', 'id', 'symbol', 'side',
                                  'entry_price', 'exit_price', 'profit_loss']
                    file = f'data/pnl/{exchange}'
                    trade_df = pd.DataFrame([trade], columns=fieldnames)
                    if path.exists(file):
                        trade_df.to_csv(
                            f"{file}/{time_stamp}.csv", header=False, index=False)
                        logger.info(f"writing the trade: {trade} to the csv!")
                    else:
                        pathlib.Path(file).mkdir(parents=True, exist_ok=True)
                        sleep(0.5)
                        trade_df.to_csv(
                            f"{file}/{time_stamp}.csv", header=False, index=False)
                        logger.info(f"writing the trade: {trade} to the csv!")

                    # Update the total profit/loss for the given symbol
                    if symbol in profit_loss:
                        profit_loss[symbol] += pnl
                        logger.info(f"{pnl}")
                    else:
                        profit_loss[symbol] = pnl
                        logger.info(f"{pnl}")

                    # Convert self.profit_loss to a DataFrame
                    df = pd.DataFrame(profit_loss.items(), columns=[
                                      'symbol', 'profit_loss'])
                    file = f'data/profit_loss/{exchange}'
                    file2 = f'data/profit_loss/date/{exchange}'
                    # Write the DataFrame to a CSV file
                    if path.exists(file):
                        if path.exists(file2):
                            df.to_csv(f'{file}/profit_loss.csv', index=False)
                            df.to_csv(f'{file2}/{time_stamp}.csv', index=False)
                            logger.info(
                                f"writing the profit/loss: {df.to_dict()} to the csv!")
                    else:
                        pathlib.Path(file).mkdir(parents=True, exist_ok=True)
                        pathlib.Path(file2).mkdir(parents=True, exist_ok=True)
                        sleep(0.5)
                        df.to_csv(f'{file}/profit_loss.csv', index=False)
                        df.to_csv(f'{file2}/{time_stamp}.csv', index=False)
                        logger.info(
                            f"writing the profit/loss: {df.to_dict()} to the csv!")

                    # Remove the trade from the trade_info list if it is closed
                    if filled_quantity == quantity:
                        trade_info.remove(trade)

    logger.info("Finished Logging the profit/loss")


def fetch_closed_orders(symbol: str, ex, logger):
    closed_order = None

    try:
        closed_order = ex.fetch_closed_orders(symbol=symbol)
    except BadSymbol as e:
        logger.error(f"this symbol is not right {symbol} - {e}")
    except Exception as e:
        logger.error(e)

    return closed_order
