from FinanceDataReader import StockListing
from preProcessor import PreProcessor
from alertDataProcess import investAlertData

kospiCode = [ticker for ticker in StockListing("KOSPI")["Symbol"] if len(ticker) <= 6]
kosdaqCode = [ticker for ticker in StockListing("KOSDAQ")["Symbol"] if len(ticker) <= 6]

processor = PreProcessor(kospiTickers=kospiCode, kosdaqTickers=kosdaqCode, startDate="2011-01-01", endDate="2020-12-31",
                             alertData=investAlertData, rollingWindow=15)

dataSet = processor.split_train_test("2018-12-31")
trainSet = dataSet[0]
testSet = dataSet[1]
