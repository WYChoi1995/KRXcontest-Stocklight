from FinanceDataReader import DataReader
from statsmodels.api import add_constant
from statsmodels.regression.rolling import RollingOLS
from pandas import DataFrame
from numpy import where, absolute, inf, nan


class PreProcessor(object):
    def __init__(self, kospiTickers: list, kosdaqTickers: list, startDate: str, endDate: str,
                 alertData: DataFrame, rollingWindow: int = 15) -> None:
        self.startDate = startDate
        self.endDate = endDate
        self.kospiTickers = kospiTickers
        self.kosdaqTickers = kosdaqTickers
        self.alertData = alertData
        self.kospiIndex = DataReader("KS11", start=self.startDate, end=self.endDate)
        self.kosdaqIndex = DataReader("KQ11", start=self.startDate, end=self.endDate)

        self.kospiTickerData = {ticker: DataReader(ticker, start=self.startDate, end=self.endDate) for ticker in kospiTickers}
        self.kosdaqTickerData = {ticker: DataReader(ticker, start=self.startDate, end=self.endDate) for ticker in kosdaqTickers}

        for ticker in self.kospiTickers:
            self.kospiTickerData[ticker]["IndexChange"] = self.kospiIndex["Change"]

        for ticker in self.kosdaqTickers:
            self.kosdaqTickerData[ticker]["IndexChange"] = self.kosdaqIndex["Change"]

        self.tickers = self.kospiTickers + self.kosdaqTickers
        self.priceData = {**self.kospiTickerData, **self.kosdaqTickerData}

        self.get_delta_price_score()
        self.get_sigma_score()
        self.get_rolling_beta(window=rollingWindow)
        self.get_volume_score(window=rollingWindow)

    @staticmethod
    def get_price_change(data: DataFrame, lag: int):
        return (data["Close"] - data["Close"].shift(lag)) / data["Close"]

    @staticmethod
    def get_tr_ratio(data: DataFrame):
        preClose = data["Close"].shift(1)
        trRatio = where((data["High"] - data["Low"]) / data["Low"] > absolute((preClose - data["High"]) / data["High"]),
                        where((data["High"] - data["Low"]) / data["Low"] > absolute((preClose - data["Low"]) / data["Low"]),
                              (data["High"] - data["Low"]) / data["Low"], absolute((preClose - data["Low"]) / data["Low"])),
                        where(absolute((preClose - data["High"]) / data["High"]) > absolute((preClose - data["Low"]) / data["Low"]),
                              absolute((preClose - data["High"]) / data["High"]), absolute((preClose - data["Low"]) / data["Low"])))

        return trRatio

    def split_train_test(self, splitDate: str):
        trainData = {ticker: self.priceData[ticker].loc[self.priceData[ticker].index <= splitDate] for ticker in self.tickers}
        testData = {ticker: self.priceData[ticker].loc[self.priceData[ticker].index > splitDate] for ticker in self.tickers}

        return trainData, testData

    def get_delta(self, data):
        return {"3D": self.get_price_change(data, 3),
                "5D": self.get_price_change(data, 5),
                "15D": self.get_price_change(data, 15)}

    def get_delta_price_score(self):
        for ticker in self.tickers:
            try:
                maxChangeDict = self.get_delta(self.priceData[ticker])
                self.priceData[ticker]["DeltaScore"] = 100 * DataFrame(maxChangeDict).dropna().max(axis=1)

            except KeyError:
                continue

    def get_volume_score(self, window=15):
        for ticker in self.tickers:
            self.priceData[ticker]["VolumeScore"] = nan
            self.priceData[ticker].reset_index(inplace=True)

            for indexNum, row in self.priceData[ticker].iterrows():
                if indexNum < 15:
                    pass

                else:
                    row["VolumeScore"] = row["Volume"] / self.priceData[ticker]["Volume"][indexNum-window: indexNum-1].median()

    def get_sigma_score(self):
        for ticker in self.tickers:
            try:
                self.priceData[ticker]["SigmaScore"] = self.get_tr_ratio(self.priceData[ticker])
                self.priceData[ticker]["SigmaScore"].replace([inf, -inf], nan)

            except KeyError:
                continue

    def get_rolling_beta(self, window: int):
        for ticker in self.tickers:
            exogVariable = add_constant(self.priceData[ticker]["IndexChange"])
            endogVariable = self.priceData[ticker]["Change"]
            rollingOLSModel = RollingOLS(endogVariable, exogVariable, window).fit()

            self.priceData[ticker]["RollingBeta"] = rollingOLSModel.params["IndexChange"]


if __name__ == "__main__":
    preProcessor = PreProcessor(kospiTickers=["005930"], kosdaqTickers=["323990"], startDate="2011-01-01", endDate="2020-12-31",
                                alertData=DataReader("005930", "2018-01-31", "2019-02-03"), rollingWindow=15)
