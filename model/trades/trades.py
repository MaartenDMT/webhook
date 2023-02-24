from ccxt.base.errors import BadSymbol, InsufficientFunds


class Trades:
    def __init__(self, logger):
        self.logger = logger

    # LONG ENTER
    def longEnter(self, exchange, symbol, get_amount, trade_info):
        try:
            order = exchange.create_market_buy_order(symbol, round(get_amount,6))
            self.logger.info(order)
            trade_info.append(
                {'exchange': exchange, 'id': order['id'], 'symbol': symbol, 'side': 'buy', 'entry_price': order['price']})
        except InsufficientFunds as e:
            self.logger.error(
                "there is not enought funding to make the trade ! - {}".format(e))
            return False
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # LONG EXIT
    def longExit(self, exchange, symbol, amount):
        try:
            order = exchange.create_market_sell_order(
                symbol, round(amount,6), {"reduceOnly": True})
            self.logger.info(order)

        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # SHORT ENTER
    def shortEnter(self, exchange, symbol, get_amount, trade_info):
        try:
            order = exchange.create_market_sell_order(symbol, round(get_amount,6))
            self.logger.info(order)
            trade_info.append(
                {'exchange': exchange, 'id': order['id'], 'symbol': symbol, 'side': 'sell', 'entry_price': order['price']})
        except InsufficientFunds as e:
            self.logger.error(
                "there is not enought funding to make the trade ! - {}".format(e))
            return False
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # SHORT EXIT
    def shortExit(self, exchange, symbol, amount):
        try:
            order = exchange.create_market_buy_order(
                symbol, round(amount,6), {"reduceOnly": True})
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True
    # TAKEPROFIT LONG #1

    def takeProfitLong1(self, exchange, symbol, get_amount, takep1):
        side = 'sell'
        order_type_tk = 'TAKE_PROFIT'
        params = {'triggerPrice': takep1,
                  'stopPrice': takep1, 'reduceOnly': True}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takep1}")

        try:
            order = exchange.createOrder(
                symbol, order_type_tk, side, round(get_amount,6), takep1, params=params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # TAKEPROFIT LONG #2

    def takeProfitLong2(self, exchange, symbol, get_amount, takep2):
        side = 'sell'
        type_o = 'TAKE_PROFIT'
        params = {'triggerPrice': takep2,
                  'reduceOnly': True, 'stopPrice': takep2}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takep2}")

        try:
            order = exchange.create_order(
                symbol, type_o, side, round(get_amount,6), takep2, params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # TAKEPROFIT LONG #3

    def takeProfitLong3(self, exchange, symbol, get_amount, takep3):
        side = 'sell'
        type_o = 'TAKE_PROFIT'
        params = {'triggerPrice': takep3,
                  'reduceOnly': True, 'stopPrice': takep3}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takep3}")

        try:
            order = exchange.create_order(
                symbol, type_o, side, round(get_amount,6), takep3, params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # STOPLOSS LONG

    def stoplossLong(self, exchange, symbol, stop,  get_amount):
        order_type_sl = 'STOP_MARKET'
        side = 'sell'
        params = {'stopPrice': stop, 'closePosition': True}
        self.logger.info(f"quantity:{get_amount}")

        try:
            order = exchange.createOrder(
                symbol, order_type_sl, side, round(get_amount,6), None, params=params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            self.logger.error("error: stoploss")
            return False

        return True

    # TAKEPROFIT SHORT #1

    def takeProfitShort1(self, exchange, symbol, get_amount, takeps1):
        side = 'buy'
        type_o = 'TAKE_PROFIT'
        params = {'triggerPrice': takeps1,
                  'reduceOnly': True, 'stopPrice': takeps1}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takeps1}")

        try:
            order = exchange.create_order(
                symbol, type_o, side, round(get_amount,6), takeps1, params=params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # TAKEPROFIT SHORT #2

    def takeProfitShort2(self, exchange, symbol, get_amount, takeps2):
        side = 'buy'
        type_o = 'TAKE_PROFIT'
        params = {'triggerPrice': takeps2,
                  'reduceOnly': True, 'stopPrice': takeps2}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takeps2}")

        try:
            order = exchange.create_order(
                symbol, type_o, side, round(get_amount,6), takeps2, params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # TAKEPROFIT SHORT #3

    def takeProfitShort3(self, exchange, symbol, get_amount, takeps3):
        side = 'buy'
        type_o = 'TAKE_PROFIT'
        params = {'triggerPrice': takeps3,
                  'reduceOnly': True, 'stopPrice': takeps3}
        self.logger.info(f"quantity:{get_amount}")
        self.logger.info(f"takeprofit :{takeps3}")

        try:
            order = exchange.create_order(
                symbol, type_o, side, round(get_amount,6), takeps3, params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    # STOPLOSS SHORT

    def stoplossShort(self, exchange, symbol, stop, get_amount):
        order_type_sl = 'STOP_MARKET'
        side = 'buy'
        params = {'stopPrice': stop, 'closePosition': True}
        self.logger.info(f"quantity:{get_amount}")

        try:
            order = exchange.createOrder(
                symbol, order_type_sl, side, None, params=params)
            self.logger.info(order)

        except Exception as e:
            self.logger.error(
                "an exception occured stoplossShort - {}".format(e))
            return False

        return True

    # stoploss_market
    def trailing_market(self, exchange, symbol, get_amount, takeps3, side):
        takeps3 = round(takeps3,3)
        side = side
        order_type = 'TRAILING_STOP_MARKET'
        rate = '0.2'
        price = None
        params = {
            'activationPrice':takeps3,
            'callbackRate': rate,
            'reduceOnly': True,
        }
        self.logger.info(f"the activantion price is : {takeps3} !")
        self.logger.info("#########################################")
        try:
            order = exchange.create_order(
                symbol, order_type, side, round(get_amount,6), price, params)
            self.logger.info(order)
        except Exception as e:
            self.logger.error(
                "an exception occured in trailing_market - {}".format(e))
            if side == "sell":
                self.takeProfitLong3(exchange, symbol, get_amount, takeps3)
                return True
            else:
                self.takeProfitShort3(exchange, symbol, get_amount, takeps3)
                return True
        return True

    
    def spot_sell(self, exchange, symbol, get_amount, price, trade_info):
        try:
            order = exchange.create_limit_sell_order(symbol, round(get_amount,6), price)
            self.logger.info(order)
            trade_info.append(
                {'exchange': exchange, 'id': order['id'], 'symbol': symbol, 'side': 'sell', 'entry_price': order['price']})
        except InsufficientFunds as e:
            self.logger.error(
                "there is not enought funding to make the trade ! - {}".format(e))
            return False
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True

    
    def spot_buy(self, exchange, symbol, get_amount, price, trade_info):
        try:
            order = exchange.create_limit_buy_order(symbol, round(get_amount,6), price)
            self.logger.info(order)
            trade_info.append(
                {'exchange': exchange, 'id': order['id'], 'symbol': symbol, 'side': 'buy', 'entry_price': order['price']})
        except InsufficientFunds as e:
            self.logger.error(
                "there is not enought funding to make the trade ! - {}".format(e))
            return False
        except Exception as e:
            self.logger.error("an exception occured - {}".format(e))
            return False

        return True