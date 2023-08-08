import io
import requests
from config import TELETOKEN, CHAT_ID

symbol_list = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'ADAUSDT', 'MATICUSDT']


def time_sleep(interval):
    """ Расчет времени ожидания для функции time.sleep()
    """
    _INTERVALS = {'1m': 1, '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
    return 60 * _INTERVALS[interval]


def send_report(image_file, message):
    """ Отправка отчетов в Telegram 
    """
    with open(image_file, 'rb') as f:
        photo = io.BytesIO(f.read())
    return requests.post(
        f'https://api.telegram.org/bot{TELETOKEN}/sendPhoto',
        data={'chat_id': CHAT_ID, 'caption': message},
        files={'photo': photo}
    )


def report_message(symbol, interval, last_price, stop_loss):
    """ Тектовое сообщение в отчете Telegram
    """
    percentage_diff = round(abs(((last_price - stop_loss) / last_price) * 100), 2)
    return '''{} \n Интервал: {} \n Stop Loss: {} %'''.format(symbol, interval, percentage_diff)
