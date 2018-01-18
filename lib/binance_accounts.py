"""
Get/Convert Balances from Binance
"""

from collections import defaultdict
from forex_python.converter import CurrencyRates
import binance
from lib.balance_common import default_to_regular
from lib.auth import binance_auth

BITCOIN = {}

def get_binance_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    binance_auth()
    all_balances = binance.balances()
    prices = binance.prices()
    bitcoin_totals = 0
    gbp_total = 0
    usd_total = 0
    currency = CurrencyRates()

    for key in all_balances:
        if float(all_balances[key]['free']) > 0:  # available currency
            result["binance"][key]["count"] = all_balances[key]["free"]

            if key != 'BTC':  # currencies that need converting to BTC
                bcoin = float(all_balances[key]['free']) * float(prices[key+'BTC'])  # value in BTC
                bitcoin_totals += float(all_balances[key]['free']) * float(prices[key+'BTC'])
            else:   #btc
                bcoin = float(all_balances[key]['free'])
                bitcoin_totals += float(bcoin)

            add_value(key, bcoin)
            usd2gbp = lambda: currency.get_rate("USD", "GBP")

            usd = bcoin *float(prices["BTCUSDT"])
            gbp = usd2gbp() * usd
            usd_total += usd
            gbp_total += gbp
            result["binance"][key]['BTC'] = bcoin
            result["binance"][key]['USD'] = usd
            result["binance"][key]["GBP"] = gbp

    usd_total = bitcoin_totals * float(prices['BTCUSDT'])
    result["binance"]["TOTALS"]["BTC"] = bitcoin_totals
    result["binance"]["TOTALS"]["USD"] = usd_total

    gbp_total = currency.get_rate("USD", "GBP") * usd_total
    result["binance"]["TOTALS"]["GBP"] = gbp_total
    add_value('USD', usd_total)
    add_value('GBP', gbp_total)

    return default_to_regular(result)

def add_value(key, value):
    """Add value to dict to save offline """
    try:
        BITCOIN[key].append(value)
    except KeyError:
        BITCOIN[key] = []
        BITCOIN[key].append(value)