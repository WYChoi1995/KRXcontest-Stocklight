from FinanceDataReader import DataReader
from numpy import where, absolute, inf, nan
from pandas import DataFrame, concat
from statsmodels.api import add_constant
from statsmodels.regression.rolling import RollingOLS


class PreProcessor(object):
    def __init__(self, kospiTickers: list, kosdaqTickers: list, startDate: str, endDate: str,
                 alertData: dict, rollingWindow: int = 15) -> None:
        self.startDate = startDate
        self.endDate = endDate
        self.kospiTickers = kospiTickers
        self.kosdaqTickers = kosdaqTickers
        self.alertData = alertData
        self.alertLabel = {"InvestCaution": 1, "InvestWarning": 2, "InvestDanger": 3}
        self.kospiIndex = DataReader("KS11", start=self.startDate, end=self.endDate)
        self.kosdaqIndex = DataReader("KQ11", start=self.startDate, end=self.endDate)

        self.kospiTickerData = {ticker: self.drop_trading_halt_day(DataReader(ticker, start=self.startDate, end=self.endDate)) for ticker in kospiTickers}
        self.kosdaqTickerData = {ticker: self.drop_trading_halt_day(DataReader(ticker, start=self.startDate, end=self.endDate)) for ticker in kosdaqTickers}

        for ticker in self.kospiTickers:
            self.kospiTickerData[ticker]["IndexChange"] = self.kospiIndex["Change"]
            self.kospiTickerData[ticker]["Multinomial"] = 0

        for ticker in self.kosdaqTickers:
            self.kosdaqTickerData[ticker]["IndexChange"] = self.kosdaqIndex["Change"]
            self.kosdaqTickerData[ticker]["Multinomial"] = 0

        self.tickers = self.kospiTickers + self.kosdaqTickers
        self.priceData = {**self.kospiTickerData, **self.kosdaqTickerData}

        '''Get independent variables'''
        self.get_delta_price_score()
        self.get_sigma_score()
        self.get_rolling_beta(window=rollingWindow)
        self.get_volume_score(window=rollingWindow)

        '''Get dependent variables'''
        self.label_alert_data()
        self.concatenatedData = self.concatenate_data()

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

    @staticmethod
    def drop_trading_halt_day(data: DataFrame):
        return data.replace(0, nan).dropna()

    @staticmethod
    def get_binomial_from_multinomial(label):
        if label == 0:
            return label

        else:
            return 1

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
                self.priceData[ticker]["DeltaScore"] = DataFrame(maxChangeDict).dropna().max(axis=1)

            except KeyError:
                continue

    def get_volume_score(self, window=15):
        for ticker in self.tickers:
            self.priceData[ticker]["VolumeScore"] = self.priceData[ticker]["Volume"] / self.priceData[ticker]["Volume"].shift(1).rolling(window=window).median()

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

    def give_label(self, alertLevel: str, labelValue: int):
        try:
            for ticker, dateList in self.alertData[alertLevel].items():
                if ticker in self.tickers:
                    data = self.priceData[ticker]

                    for date in dateList:
                        if date[0] == date[1]:
                            data.loc[data.index == date[0], "Multinomial"] = labelValue

                        else:
                            data.loc[(data.index >= date[0]) & (data.index <= date[1]), "Multinomial"] = labelValue

                else:
                    pass

        except KeyError:
            pass

    def label_alert_data(self):
        for alertLevel, labelValue in self.alertLabel.items():
            self.give_label(alertLevel, labelValue)

    def concatenate_data(self):
        tickerData = {**self.kospiTickerData, **self.kosdaqTickerData}
        concatenatedData = concat([tickerData[ticker] for ticker in tickerData.keys()])
        concatenatedData["Binomial"] = concatenatedData["Multinomial"].map(lambda label: self.get_binomial_from_multinomial(label))

        return concatenatedData
