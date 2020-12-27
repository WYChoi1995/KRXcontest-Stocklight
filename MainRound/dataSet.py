from FinanceDataReader import StockListing, DataReader
from preProcessor import PreProcessor

kospiCode = [ticker for ticker in StockListing("KOSPI")["Symbol"] if len(ticker) <= 6]
kosdaqCode = [ticker for ticker in StockListing("KOSDAQ")["Symbol"] if len(ticker) <= 6]

priceData = PreProcessor(kospiTickers=["005930"], kosdaqTickers=["323990"], startDate="2011-01-01", endDate="2020-12-31",
                         alertData=DataReader("005930", "2018-01-31", "2019-02-03"), rollingWindow=15)
