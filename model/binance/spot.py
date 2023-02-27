import logging

from model.trades.trades import Trades
from tickets import spot_base, spot_ticks
from utils.trade_logger import add_log_info
from utils.util import (get_max_position_available_s, in_position_check_s,
                        start_thread)

trade_info = []
profit_loss = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BinanceSpot:
    def __init__(self, exchange, symbol: str, side: int, ProcessingMoney: float):

        self.takeprofit1: bool = False
        self.takeprofit2: bool = False
        self.takeprofit3: bool = False
        self.get_amount: float = 0

        self.stop = 7
        self.tp1 = 10

        add_log_info(logger, exchange)
        self.logger = logger
        self.thread = None
        self.trade_info = trade_info
        self.profit_loss = profit_loss
        self.trades = Trades(self.logger)
        
        #starting the trading function
        self.logger.info("SPOT LOGGER ACTIVE")
        self.trading(exchange, symbol, side, ProcessingMoney)

        #starting the thread
        start_thread(exchange, symbol, self.profit_loss, self.trade_info,
                     self.thread, self.logger)

    def trading(self, exchange, symbol: str, side: int, ProcessingMoney: float):

        self.logger.info(f"exchange: {exchange.name} ")
        
        #getting the quote and base, checking the usdt balance and symbol balance and price
        ticker = spot_ticks[symbol]
        tick = spot_base[ticker]
        usdt_balance, ticker_balance, price = in_position_check_s(
            exchange, symbol, tick, self.logger)

        #translating the symbol to usdt balance
        ticker_to_usdt = ticker_balance * price

        print(f"the ticker amount in usdt: {ticker_to_usdt}")

        if usdt_balance > 20 and ticker_to_usdt > 20:
            
            # setting leverage and cancel all the open orders
            leverage = 1
            exchange.cancel_all_orders(symbol)

            #BULL EVENT
            if side == 1:

                # get the amount to enter a trade
                get_amount = get_max_position_available_s(
                    exchange, 'USDT', symbol, leverage, ProcessingMoney)

                # long trade
                self.logger.info(f"ENTERING LONG POSITION WITH: {get_amount}")
                l = self.trades.spot_buy(
                    exchange, symbol, get_amount, price, self.trade_info)

                # stoplos for long trade (might be implemented in the futures depending on the bots performances)
                # stop = price - (price / 100 * self.stop)
                # self.trades.stoplossShort(exchange, symbol, stop, get_amount)

                # Take profit Long
                amount = get_amount / 2
                takep1 = (price / 100 * self.tp1) + price
                self.trades.trailing_market(
                    exchange, symbol, amount, takep1, 'sell')

            #BEAR EVENT
            elif side == -1:

                # get the emount to exit the trade
                get_amount = get_max_position_available_s(
                    exchange, tick, symbol, leverage, ProcessingMoney)

                # short trade
                self.logger.info(f"ENTERING SHORT POSITION WITH: {get_amount}")
                l = self.trades.spot_sell(
                    exchange, symbol, get_amount, price, self.trade_info)

                # Take profit Short
                amount = get_amount / 2
                takep1 = price - (price / 100 * self.tp1)
                self.trades.trailing_market(
                    exchange, symbol, amount, takep1, 'sell')
