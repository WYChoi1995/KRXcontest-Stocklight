import plotly.graph_objects as go
from pandas import read_csv
from koreanToEng import *


class StockPlotter(object):
    def __init__(self, marketDataFile):
        self.marketData = read_csv(marketDataFile, index_col=KoreanName)
        self.upColor = "#981220"
        self.downColor = "#11457F"
        self.colorTable = {True: self.upColor, False: self.downColor}

    @staticmethod
    def get_color_line(color):
        return {"line": {"color": color}}

    @staticmethod
    def get_marker(colors):
        return {"color": colors}

    @staticmethod
    def get_layout(title=""):
        xAxis = go.layout.XAxis(title=go.layout.xaxis.Title(text="Time (KST - Korea)"), rangeslider={"visible": False})
        yAxis = {"title": "Volume", "domain": [0, 0.2], "showticklabels": True}
        yAxis2 = {"title": "Price", "domain": [0.2, 0.8], "showticklabels": True}

        return {"title": title, "plot_bgcolor": "rgb(245, 245, 245)", "xaxis": xAxis, "yaxis": yAxis,
                "yaxis2": yAxis2, "margin": {"t": 40, "b": 40, "r": 40, "l": 40}}

    def get_volume_chart(self, df):
        colorTable = {True: "#981220", False: "#11457F"}
        volumeColor = [colorTable[boolValue] for boolValue in (df["Volume"] > df["Volume"].shift(1)).to_list()]
        volumeChart = {"type": "bar", "x": df.index, "y": df["Volume"], "marker": self.get_marker(volumeColor), "name": "Volume"}

        return volumeChart

    def get_candle_chart(self, df):
        candleStick = {"type": "candlestick", "open": df["Open"], "high": df["High"], "low": df["Low"], "Close": df["Close"],
                       "x": df.index, "yaxis": "y2", "name": "GS", "increasing": self.get_color_line(self.upColor),
                       "decreasing": self.get_color_line(self.downColor)}

        return [candleStick]

    def get_chart(self, df):
        return [self.get_candle_chart(df), self.get_volume_chart(df)]

    def plot_chart(self, df, title):
        figure = go.Figure(data=self.get_chart(df), layout=self.get_layout(title=title))
        figure.show()
