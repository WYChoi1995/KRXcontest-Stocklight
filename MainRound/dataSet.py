from FinanceDataReader import StockListing
from preProcessor import PreProcessor
from pandas import DataFrame
from korToEng import SPAC
from alertDataProcess import investAlertData


def eliminate_spac(stockListed: DataFrame):
    return stockListed[~stockListed["Name"].str.contains(SPAC)]


kospiList = eliminate_spac(StockListing("KOSPI"))
kosdaqList = eliminate_spac(StockListing("KOSDAQ"))

kospiCode = [ticker for ticker in kospiList["Symbol"] if len(ticker) <= 6]
kosdaqCode = [ticker for ticker in kosdaqList["Symbol"] if len(ticker) <= 6]

processor = PreProcessor(kospiTickers=kospiCode, kosdaqTickers=kosdaqCode, startDate="2016-01-01", endDate="2020-12-31",
                         alertData=investAlertData, rollingWindow=15)

dataSet = processor.split_train_test("2019-12-31")
trainSet = dataSet[0]
testSet = dataSet[1]
