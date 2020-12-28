import plotly.graph_objects as go
from FinanceDataReader import DataReader
from pandas import read_csv, DataFrame

from koreanToEng import *


class StockPlotter(object):
    def __init__(self, marketDataFile):
        self.marketData = read_csv(marketDataFile, index_col=KoreanName)
        self.upColor = "#981220"
        self.downColor = "#11457F"
        self.colorTable = {True: self.upColor, False: self.downColor}

    @staticmethod
    def get_color_line(color: str):
        return {"line": {"color": color}}

    @staticmethod
    def get_marker(colors: list):
        return {"color": colors}

    @staticmethod
    def get_layout(title: str = ""):
        xAxis = go.layout.XAxis(title=go.layout.xaxis.Title(text="Time (KST - Korea)"), rangeslider={"visible": False})
        yAxis = {"title": "Volume", "domain": [0, 0.2], "showticklabels": True}
        yAxis2 = {"title": "Price", "domain": [0.2, 0.8], "showticklabels": True}

        return {"title": title, "plot_bgcolor": "rgb(245, 245, 245)", "xaxis": xAxis, "yaxis": yAxis,
                "yaxis2": yAxis2, "margin": {"t": 40, "b": 40, "r": 40, "l": 40}}

    def get_volume_chart(self, marketData: DataFrame):
        colorTable = {True: "#981220", False: "#11457F"}
        volumeColor = [colorTable[boolValue] for boolValue in (marketData["Volume"] > marketData["Volume"].shift(1)).to_list()]
        volumeChart = {"type": "bar", "x": marketData.index, "y": marketData["Volume"], "marker": self.get_marker(volumeColor), "name": "Volume"}

        return volumeChart

    def get_candle_chart(self, marketData: DataFrame):
        candleChart = {"type": "candlestick", "open": marketData["Open"], "high": marketData["High"], "low": marketData["Low"], "close": marketData["Close"],
                       "x": marketData.index, "yaxis": "y2", "name": "Candle", "increasing": self.get_color_line(self.upColor),
                       "decreasing": self.get_color_line(self.downColor)}

        return candleChart

    @staticmethod
    def get_market_data(issueCode: str, start: str, end: str):
        data = DataReader(symbol=issueCode, start=start, end=end)

        for index, row in data.iterrows():
            if row["Open"] == 0:
                data.at[index, "Open"] = row["Close"]
                data.at[index, "High"] = row["Close"]
                data.at[index, "Low"] = row["Close"]

            else:
                pass

        return data

    def get_chart(self, marketData: DataFrame):
        return [self.get_candle_chart(marketData), self.get_volume_chart(marketData)]

    def plot_chart(self, marketData: DataFrame, title: str = ""):
        figure = go.Figure(data=self.get_chart(marketData), layout=self.get_layout(title=title))
        figure.show()
