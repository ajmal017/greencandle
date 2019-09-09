# pylint: disable=no-member

"""
Perform run for test & prod
"""

import os
import time
import pickle
import gzip
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from pathlib import Path
import binance
from str2bool import str2bool
from .engine import Engine
from .redis_conn import Redis
from .mysql import Mysql
from .profit import get_recent_profit
from .order import Trade
from .binance_common import get_dataframes
from .logger import getLogger, get_decorator

from . import config
LOGGER = getLogger(__name__, config.main.logging_level)
CHUNK_SIZE = 200
GET_EXCEPTIONS = get_decorator((Exception))

@GET_EXCEPTIONS
def serial_test(pairs, intervals, data_dir, indicators):
    """
    Do test with serial data
    """
    LOGGER.debug("Performaing serial run")

    for pair in pairs:
        for interval in intervals:
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            del dbase
            redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[interval]
            redis = Redis(interval=interval, test=True, db=redis_db)
            redis.clear_all()
            del redis

        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir, indicators)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    """Serial test loop"""
    redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[interval]
    LOGGER.debug("Serial run %s %s %s", pair, interval, redis_db)
    redis = Redis(interval=interval, test=True, db=redis_db)
    filename = glob("{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s", filename, pair, interval)
        return
    if filename.endswith("gz"):
        handle = gzip.open(filename, "rb")
    else:
        handle = open(filename, "rb")
    dframe = pickle.load(handle)
    handle.close()

    prices_trunk = {pair: "0"}
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.debug("IN LOOP %s ", beg)
        trade = Trade(interval=interval, test_trade=True, test_data=True)

        sells = []
        buys = []
        end = beg + CHUNK_SIZE
        LOGGER.debug("chunk: %s, %s", beg, end)
        dataframe = dframe.copy()[beg: end]

        current_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.gmtime(int(dataframe.iloc[-1].closeTime)/1000))
        LOGGER.debug("current date: %s", current_time)
        if len(dataframe) < CHUNK_SIZE:
            LOGGER.debug("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(prices=prices_trunk, dataframes=dataframes,
                        interval=interval, test=True, db=redis_db)
        engine.get_data(localconfig=indicators)

        ########TEST stategy############
        result, current_time, current_price = redis.get_action(pair=pair, interval=interval)
        LOGGER.debug('In Strategy %s', result)
        if 'SELL' in result or 'BUY' in result:
            LOGGER.debug('Strategy - Adding to redis')
            scheme = {}
            scheme["symbol"] = pair
            scheme["direction"] = result
            scheme['result'] = 0
            scheme['data'] = result
            scheme["event"] = "trigger"
            engine.add_scheme(scheme)
        ################################

        del engine

        if result == "BUY":
            buys.append((pair, current_time, current_price))
            LOGGER.debug("Items to buy: %s", buys)
            trade.buy(buys)
        elif result == "SELL":
            sells.append((pair, current_time, current_price))
            LOGGER.debug("Items to sell: %s", sells)
            trade.sell(sells)

    del redis
    LOGGER.info("Selling remaining items")
    sells = []
    sells.append((pair, current_time, current_price))
    trade.sell(sells)

def parallel_test(pairs, interval, redis_db, data_dir, indicators):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s", interval)
    redis = Redis(interval=interval, test=True, db=redis_db)

    trade = Trade(interval=interval, test_trade=True, test_data=True)
    redis.clear_all()
    dframes = {}
    sizes = []
    for pair in pairs:
        filename = glob("/{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
        if not os.path.exists(filename):
            LOGGER.critical("Cannot find file: %s", filename)
            continue
        if filename.endswith("gz"):
            handle = gzip.open(filename, "rb")
        else:
            handle = open(filename, "rb")

        dframes[pair] = pickle.load(handle)
        sizes.append(len(dframes[pair]))
        LOGGER.info("%s dataframe size: %s", pair, len(dframes[pair]))
        handle.close()

    LOGGER.critical(dframes.keys())
    for beg in range(max(sizes) - CHUNK_SIZE):
        end = beg + CHUNK_SIZE
        dataframes = {}
        buys = []
        sells = []
        for pair in pairs:
            LOGGER.info("Current loop: %s to %s pair:%s", beg, end, pair)
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True, db=redis_db)
            engine.get_data(localconfig=indicators)

            ########TEST stategy############
            result, current_time, current_price = redis.get_action(pair=pair, interval=interval)
            LOGGER.info('In Strategy %s', result)
            if 'SELL' in result or 'BUY' in result:
                LOGGER.info('Strategy - Adding to redis')
                scheme = {}
                scheme["symbol"] = pair
                scheme["direction"] = result
                scheme['result'] = 0
                scheme['data'] = result
                scheme["event"] = "trigger"
                engine.add_scheme(scheme)
            ################################

            del engine

            if result == "BUY":
                LOGGER.debug("Items to buy")
                buys.append((pair, current_time, current_price))
            if result == "SELL":
                LOGGER.debug("Items to sell")
                sells.append((pair, current_time, current_price))
        trade.sell(sells)
        trade.buy(buys)

    print(get_recent_profit(True, interval=interval))

def prod_loop(interval, test):
    """
    Loop through collection cycle (PROD)
    """
    main_indicators = config.main.indicators.split()
    main_pairs = config.main.pairs.split()
    dbase = Mysql(test=False, interval=interval)
    additional_pairs = dbase.get_trades()
    del dbase
    # get unique list of pairs in config,
    #and those currently in an active trade
    print(type(main_pairs))
    print(type(additional_pairs))
    pairs = list(set(main_pairs + additional_pairs))
    LOGGER.info("Pairs DB: %s", additional_pairs)
    LOGGER.info("Pairs in config: %s", main_pairs)
    LOGGER.info("Total unique pairs: %s", len(pairs))

    max_trades = int(config.main.max_trades)
    test_trade = test if test else str2bool(config.main.test_trade)

    LOGGER.info("Starting new cycle")
    Path('/var/run/greencandle').touch()
    LOGGER.debug("max trades: %s", max_trades)

    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=interval)

    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval)
    engine.get_data(localconfig=main_indicators)
    redis = Redis(interval=interval, test=False, db=0)
    buys = []
    sells = []
    for pair in pairs:
        ########TEST stategy############
        result, current_time, current_price = redis.get_action(pair=pair, interval=interval)
        LOGGER.info('In Strategy %s', result)
        if 'SELL' in result or 'BUY' in result:
            LOGGER.info('Strategy - Adding to redis')
            scheme = {}
            scheme["symbol"] = pair
            scheme["direction"] = result
            scheme['result'] = 0
            scheme['data'] = result
            scheme["event"] = "trigger"
            engine.add_scheme(scheme)
            del engine
        ################################

        if result == "BUY":
            LOGGER.debug("Items to buy")
            buys.append((pair, current_time, current_price))
        if result == "SELL":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price))
    trade = Trade(interval=interval, test_trade=test_trade, test_data=False)
    trade.sell(sells)
    trade.buy(buys)

    del redis