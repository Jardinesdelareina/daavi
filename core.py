import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import CLIENT
from utils import send_report, time_sleep, report_message


class BinanceAPI:

    def __init__(self, symbol, interval):
        self.symbol = symbol
        self.interval = interval
        self.report_file = f'reports/{self.symbol}.png'
    

    def get_data(self):
        """ Получение данных
        """
        df = pd.DataFrame(CLIENT.get_historical_klines(
            symbol=self.symbol, 
            interval=self.interval, 
            limit=50
        ))
        df = df.iloc[:,:5]
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close']
        df = df.set_index('Time')
        df.index = pd.to_datetime(df.index, unit='ms')
        df = df.astype(float)
        return df


class CCI(BinanceAPI):

    def get_cci_values(self, period: int) -> float:
        """ Расчет индикатора CCI 
        
            period (int): Период индикатора, на основании которого производится расчет значений
        """
        df = self.get_data()
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        rolling_mean = typical_price.rolling(window=period).mean()
        rolling_std = typical_price.rolling(window=period).std()
        indicator = round((typical_price - rolling_mean) / (0.015 * rolling_std), 2)
        return indicator


    def get_report(self):
        """ Создание графического отчета, печать состояния индикатора
        """
        df = self.get_data()

        """ Создание единого пространства для нескольких объектов:
            две строки, одна колонка, общая ось x для двух подграфиков
        """
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

        """ Добавление подграфиков в общее пространство
            1. Японские свечи
            2. Индикатор CCI с периодом 14
            3. Индикатор CCI с периодом 6
        """
        fig.add_trace(go.Candlestick(x=df.index,
                                    open=df['Open'],
                                    high=df['High'],
                                    low=df['Low'],
                                    close=df['Close'],
                                    increasing_line_color='green',
                                    decreasing_line_color='red',
                                    showlegend=False
                                    ),
                                    row=1,
                                    col=1
                                    )
        fig.add_trace(go.Scatter(
                            x=df.index, 
                            y=self.get_cci_values(14),
                            mode='lines', 
                            line=dict(width=2), 
                            marker=dict(color='black'),
                            showlegend=False
                            ), 
                            row=2,
                            col=1
        )
        fig.add_trace(go.Scatter(
                            x=df.index, 
                            y=self.get_cci_values(6),
                            mode='lines', 
                            line=dict(width=1), 
                            marker=dict(color='teal'),
                            showlegend=False
                            ),
                            row=2,
                            col=1
        )

        """ Отклчение бегунка под свечным графиком
        """
        fig.update(layout_xaxis_rangeslider_visible=False)

        """ Настройки общего пространства:
            шкалы измерения графиков справа, фон белый, title пространства - название переменной SYMBOL,
            добавление нулевой линии на подграфик (цвет серый, толщина 1)
        """
        fig.update_layout(
            yaxis=dict(side='right'),
            yaxis2=dict(side='right'),
            paper_bgcolor='white', 
            plot_bgcolor='white', 
            title_text=f'{self.symbol}',
            shapes=[
                dict(
                    type='line', yref='y2', xref='paper',
                    x0=0, y0=0, x1=1, y1=0,
                    line=dict(
                        color='grey',
                        width=1,
                    )
                )
            ]
        )

        """ Запись изображения в формате .png
        """
        fig.write_image(self.report_file)


    def main(self):
        print(f'CCI Informer {self.symbol} Start')
        while True:
            df = self.get_data()
            df['CCI_14'] = self.get_cci_values(14)
            df['CCI_6'] = self.get_cci_values(6)

            # Пять последних значений CCI выше/ниже нуля, формирование тренда
            green_zone = all(cci > 0 for cci in df['CCI_14'][-5:]) or \
                (sum(1 for cci in df['CCI_14'][-5:] if cci < 0) < 5)
            red_zone = all(cci < 0 for cci in df['CCI_14'][-5:]) or \
                (sum(1 for cci in df['CCI_14'][-5:] if cci > 0) < 5)

            # ZLR
            green_zlr = green_zone and (
                (df.CCI_6.iloc[-2] < 0) and \
                (df.CCI_6.iloc[-1] > 0) and \
                (df.CCI_14.iloc[-1] > 0)
            )
            red_zlr = red_zone and (
                (df.CCI_6.iloc[-2] > 0) and \
                (df.CCI_6.iloc[-1] < 0) and \
                (df.CCI_14.iloc[-1] < 0)
            )

            # Одновременное пересечение всеми CCI нуля
            green_zero_line = all(df[f'CCI_{period}'].iloc[-2] < 0 for period in [14, 6]) and \
                all(df[f'CCI_{period}'].iloc[-1] > 0 for period in [14, 6])
            red_zero_line = all(df[f'CCI_{period}'].iloc[-2] > 0 for period in [14, 6]) and \
                all(df[f'CCI_{period}'].iloc[-1] < 0 for period in [14, 6])
            
            # Пересечение 100/-100 в обратном направлении (ложная волна)
            green_100 = any(cci < 100 for cci in df['CCI_14'][-5:-2]) and \
                (df.CCI_14.iloc[-3] < df.CCI_14.iloc[-2]) and \
                (df.CCI_14.iloc[-2] > 100) and (df.CCI_14.iloc[-1] < 100)
            red_100 = any(cci > -100 for cci in df['CCI_14'][-5:-2]) and \
                (df.CCI_14.iloc[-3] > df.CCI_14.iloc[-2]) and \
                (df.CCI_14.iloc[-2] < -100) and (df.CCI_14.iloc[-1] > -100)

            if green_zlr or red_zlr or green_zero_line or red_zero_line or green_100 or red_100:
                print(f'{self.symbol} Alert')
                self.get_report()
                send_report(
                    image_file=self.report_file,
                    message=report_message(
                        symbol=self.symbol,
                        interval=self.interval,
                        last_price=df.Close.iloc[-1], 
                        stop_loss=df.Low.iloc[-2] if green_zlr or green_zero_line or green_100 else df.High.iloc[-2]
                    )
                )
            else:
                print(f'{self.symbol} Ожидание')
            time.sleep(time_sleep(interval=self.interval))
            