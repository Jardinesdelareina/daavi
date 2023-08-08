import threading
from core import CCI
from utils import symbol_list


def start_all_informer(interval):
    threads = []
    for ticker in symbol_list:
        bot = CCI(symbol=ticker, interval=interval)
        t = threading.Thread(target=bot.main)
        threads.append(t)
        t.start()


def start_single_informer(symbol, interval):
    bot = CCI(symbol, interval)
    bot.main()


#start_single_informer('BTCUSDT', '30m')
start_all_informer('30m')
