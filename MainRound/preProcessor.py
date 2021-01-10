from FinanceDataReader import DataReader
from numpy import where, absolute, inf, nan
from pandas import DataFrame, concat, read_csv, to_datetime
from statsmodels.api import add_constant
from statsmodels.regression.rolling import RollingOLS


class PreProcessor(object):
    def __init__(self, kospiTickers: list, kosdaqTickers: list, alertData: dict, startDate: str = "2016-01-01", endDate: str = "2020-12-30",
                 rollingWindow: int = 15) -> None:
        self.startDate = startDate
        self.endDate = endDate
        self.kospiTickers = kospiTickers
        self.kosdaqTickers = kosdaqTickers
        self.alertData = alertData
        self.alertLabel = {"InvestCaution": 1, "InvestWarning": 2, "InvestDanger": 3}
        self.kospiIndex = DataReader("KS11", start=self.startDate, end=self.endDate)
        self.kosdaqIndex = DataReader("KQ11", start=self.startDate, end=self.endDate)
        self.riskFree = read_csv("./csvData/riskFree.csv", index_col="Date")
        self.riskFree.index = to_datetime(self.riskFree.index)

        self.priceDataKOSPI = {ticker: self.drop_trading_halt_day(DataReader(ticker, start=self.startDate, end=self.endDate))
                               for ticker in kospiTickers}
        self.priceDataKOSDAQ = {ticker: self.drop_trading_halt_day(DataReader(ticker, start=self.startDate, end=self.endDate))
                                for ticker in kosdaqTickers}

        for ticker in self.kospiTickers:
            self.priceDataKOSPI[ticker]["IssueCode"] = "A" + ticker
            self.priceDataKOSPI[ticker]["IndexRiskPremium"] = (self.kospiIndex["Change"] - self.riskFree["RiskFree"]).dropna()
            self.priceDataKOSPI[ticker]["RiskPremium"] = (self.priceDataKOSPI[ticker]["Change"] - self.riskFree["RiskFree"]).dropna()
            self.priceDataKOSPI[ticker]["Multinomial"] = 0

        for ticker in self.kosdaqTickers:
            self.priceDataKOSDAQ[ticker]["IssueCode"] = "A" + ticker
            self.priceDataKOSDAQ[ticker]["IndexRiskPremium"] = (self.kosdaqIndex["Change"] - self.riskFree["RiskFree"]).dropna()
            self.priceDataKOSDAQ[ticker]["RiskPremium"] = (self.priceDataKOSDAQ[ticker]["Change"] - self.riskFree["RiskFree"]).dropna()
            self.priceDataKOSDAQ[ticker]["Multinomial"] = 0

        self.tickers = self.kospiTickers + self.kosdaqTickers
        self.priceData = {**self.priceDataKOSPI, **self.priceDataKOSDAQ}
        self.variableList = ["IssueCode", "RollingBeta", "DeltaScore", "VolumeScore", "SigmaScore", "Multinomial"]

        '''Get independent variables'''
        self.get_delta_price_score()
        self.get_sigma_score()
        self.get_rolling_beta(window=rollingWindow)
        self.get_volume_score(window=rollingWindow)

        '''Get dependent variables'''
        self.label_alert_data()
        self.concatenatedData = self.concatenate_data(variableList=self.variableList)

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
        trainData = self.concatenatedData.loc[self.concatenatedData.index <= splitDate]
        testData = self.concatenatedData.loc[self.concatenatedData.index > splitDate]

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
            try:
                if len(self.priceData[ticker]) > window:
                    exogVariable = add_constant(self.priceData[ticker]["IndexRiskPremium"])
                    endogVariable = self.priceData[ticker]["RiskPremium"]
                    rollingOLSModel = RollingOLS(endogVariable, exogVariable, window).fit()

                    self.priceData[ticker]["RollingBeta"] = rollingOLSModel.params["IndexRiskPremium"]

                else:
                    self.priceData[ticker]["RollingBeta"] = nan

            except ValueError:
                self.priceData[ticker]["RollingBeta"] = nan

    def give_label(self, alertLevel: str, labelValue: int):
        for ticker, dateList in self.alertData[alertLevel].items():
            if ticker in self.tickers:
                try:
                    data = self.priceData[ticker]

                    for date in dateList:
                        if date[0] == date[1]:
                            data.loc[data.index == date[0], "Multinomial"] = labelValue

                        else:
                            data.loc[(data.index >= date[0]) & (data.index <= date[1]), "Multinomial"] = labelValue

                except KeyError:
                    pass

            else:
                pass

    def label_alert_data(self):
        for alertLevel, labelValue in self.alertLabel.items():
            self.give_label(alertLevel, labelValue)

    def concatenate_data(self, variableList: list):
        tickerData = {**self.priceDataKOSPI, **self.priceDataKOSDAQ}
        concatenatedData = concat([tickerData[ticker][variableList] for ticker in self.tickers])
        concatenatedData["Binomial"] = concatenatedData["Multinomial"].map(lambda label: self.get_binomial_from_multinomial(label))

        return concatenatedData.dropna()
