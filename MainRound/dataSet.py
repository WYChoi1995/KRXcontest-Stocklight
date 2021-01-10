from FinanceDataReader import StockListing
from pandas import DataFrame

from alertDataProcess import investAlertData
from korToEng import SPAC
from preProcessor import PreProcessor


def eliminate_spac(stockListed: DataFrame):
    return stockListed[~stockListed["Name"].str.contains(SPAC)]


kospiList = eliminate_spac(StockListing("KOSPI"))
kosdaqList = eliminate_spac(StockListing("KOSDAQ"))

kospiCode = [ticker for ticker in kospiList["Symbol"] if len(ticker) <= 6]
kosdaqCode = [ticker for ticker in kosdaqList["Symbol"] if len(ticker) <= 6]

processor = PreProcessor(kospiTickers=kospiCode, kosdaqTickers=kosdaqCode, startDate="2016-01-01", endDate="2020-12-30",
                         alertData=investAlertData, rollingWindow=15)

processor.concatenatedData.to_csv("DataSet.csv")
