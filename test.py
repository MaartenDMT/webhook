import logging
import os
from time import sleep

from binance import Client
from dotenv import load_dotenv

path = '.env'
load_dotenv(path)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

balances = {}


class ClientHelper:
    def __init__(self, client) -> None:
        self.client = client

    def _format(self, value, decimal=2) -> str:
        return format(float(value), f".{decimal}f")

    def transfer_futures_to_spot(self, amount) -> None:
        self.client.futures_account_transfer(
            asset="USDT", amount=float(amount), type="2")

    def transfer_spot_to_futures(self, amount) -> None:
        self.client.futures_account_transfer(
            asset="USDT", amount=float(amount), type="1")

    def transfer_spot_to_margin(self, amount) -> None:
        self.client.transfer_spot_to_margin(
            asset="USDT", amount=float(amount), type="1")

    def get_balance_margin_USDT(self) -> float:
        try:
            margin_account = self.client.get_margin_account()
            _len = len(margin_account["userAssets"])
            for x in range(_len):
                if margin_account["userAssets"][x]["asset"] == "USDT":
                    balance_USDT = margin_account["userAssets"][x]["free"]
                    return float(balance_USDT)
        except:
            pass

        return 0

    def spot_balance(self) -> float:
        sum_btc = 0.0
        balances = self.client.get_account()
        for _balance in balances["balances"]:
            asset = _balance["asset"]
            if float(_balance["free"]) != 0.0 or float(_balance["locked"]) != 0.0:
                try:
                    btc_quantity = float(
                        _balance["free"]) + float(_balance["locked"])
                    if asset == "BTC":
                        sum_btc += btc_quantity
                    else:
                        _price = self.client.get_symbol_ticker(
                            symbol=asset + "BTC")
                        sum_btc += btc_quantity * float(_price["price"])
                except:
                    pass

        current_btc_price_USD = self.client.get_symbol_ticker(symbol="BTCUSDT")[
            "price"]
        own_usd = sum_btc * float(current_btc_price_USD)
        print(" * Spot => %.8f BTC == " % sum_btc, end="")
        print("%.8f USDT" % own_usd)

        for balance in balances["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = balance["free"]
                return float(usdt_balance)

    def get_futures_usdt(self, is_both=False) -> float:
        futures_usd = 0.0
        assets = self.client.futures_account_balance()
        for asset in assets:
            name = asset["asset"]
            balance = float(asset["balance"])
            if name == "USDT":
                futures_usd += balance

            if name == "BNB" and is_both:
                current_bnb_price_USD = self.client.get_symbol_ticker(symbol="BNBUSDT")[
                    "price"]
                futures_usd += balance * float(current_bnb_price_USD)

        return float(futures_usd)

    def _get_futures_usdt(self) -> str:
        """USDT in Futures, unRealizedProfit is also included"""
        futures_usd = self.get_futures_usdt(is_both=False)
        futures = self.client.futures_position_information()
        open_position_count = 0
        for future in futures:
            if future["positionAmt"] != "0" and float(future["unRealizedProfit"]) != 0.00000000:
                futures_usd += float(future["unRealizedProfit"])
                open_position_count += 1
                print(future)
                print(f'PNL: {future["unRealizedProfit"]}')
                print("-"*20)
                    
        return format(futures_usd, ".2f")


def main(client_helper: ClientHelper) -> None:

    while True:
        print("getting the balances")

        futures_usd = client_helper._get_futures_usdt()
        usdt_balance = client_helper.spot_balance()
        margin_usdt = client_helper.get_balance_margin_USDT()

        print(
            f" * Futures={futures_usd} USD | SPOT={client_helper._format(usdt_balance)} USD | MARGIN={margin_usdt}")
        print("#"*65)
        sleep(120)


# exchange.set_sandbox_mode(True)
if __name__ == "__main__":
    api_key = os.environ.get('D_BIN_KEY')
    api_secret = os.environ.get('D_BIN_SECRET')
    client = Client(api_key, api_secret)
    client_helper = ClientHelper(client)
    main(client_helper)
