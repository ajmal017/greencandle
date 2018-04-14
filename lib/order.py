#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

"""
Test Buy/Sell orders
"""

from __future__ import print_function
import os
import time
import sys

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)


import binance
from lib.auth import binance_auth
from lib.logger import getLogger
from lib.config import get_config
from lib.mysql import Mysql
from lib.profit import get_quantity
from lib.balance import get_balance

LOGGER = getLogger(__name__)
PRICE_PER_TRADE = int(get_config("backend")["price_per_trade"])
MAX_TRADES = int(get_config("backend")["max_trades"])
INTERVAL = str(get_config("backend")["interval"])
INVESTMENT = float(get_config("backend")["investment"])
RATE = float(get_config("backend")["rate"])

binance_auth()

def get_buy_price(pair=None):
    """ return lowest buying request """
    return sorted([float(i) for i in binance.depth(pair)["asks"].keys()])[0]

def get_sell_price(pair=None):
    """ return highest selling price """
    return sorted([float(i) for i in binance.depth(pair)["bids"].keys()])[-1]

def buy(buy_list, test_data=False, test_trade=True):
    """
    Buy as many items as we can from buy_list depending on max amount of trades, and current
    balance in BTC
    """
    LOGGER.debug("We have %s potential items to buy", len(buy_list))
    if buy_list:
        dbase = Mysql(test=False, interval=INTERVAL)
        if test_data:
            current_btc_bal = 5000
        else:
            current_btc_bal = get_balance()['binance']['BTC']['BTC']

        amount_to_buy_btc = INVESTMENT * RATE

        #current_btc_bal = events.balance["binance"]["BTC"]["count"]

        for item in buy_list:

            current_trades = dbase.get_trades()
            avail_slots = MAX_TRADES - len(current_trades)
            btc_amount = current_btc_bal / avail_slots
            cost = float(binance.princes()[item])
            amount = btc_amount / cost

            if float(amount_to_buy_btc) > float(current_btc_bal):
                LOGGER.warning("Unable to purchase %s, insufficient funds", item)
                break
            elif len(current_trades) >= MAX_TRADES:
                LOGGER.warning("Too many trades, skipping")
                break
            elif item in current_trades:
                LOGGER.warning("We already have a trade of %s, skipping...", item)
                continue
            else:
                LOGGER.info("Buying item %s", item)
                price = float(binance.prices()[item])
                dbase.insert_trade(item, price, amount_to_buy_btc, INVESTMENT, total=amount)
                if not test_data:
                    binance.order(symbol=item, side=binance.BUY, quantity=amount,
                                  orderType="MARKET", test=test_trade)
    else:
        LOGGER.info("Nothing to buy")

def sell(sell_list, test_data=False, test_trade=True):
    """
    Sell items in sell_list
    """

    if sell_list:
        LOGGER.info("We need to sell %s", sell_list)
        dbase = Mysql(test=False, interval=INTERVAL)
        for item in sell_list:
            quantity = dbase.get_quantity(item)
            price = binance.prices()[item]
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            dbase.update_trades(pair=item, sell_time=current_time,
                                sell_price=price)
            if not test_data:
                binance.order(symbol=item, side=binance.SELL, quantity=quantity,
                              orderType="MARKET", test=test_trade)
    else:
        LOGGER.info("No items to sell")

def main():
    """ Main function """
    print("ask (buying price from):", get_buy_price())
    print("bid (selling price to):", get_sell_price())

if __name__ == "__main__":
    main()
