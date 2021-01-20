from pandas import read_csv

from alertDataProcess import investAlertData
from preProcessor import PreProcessor

tickerData = read_csv("./csvData/firmList.csv")

kospiCode = [ticker for ticker in tickerData.loc[tickerData["Market"] == "KOSPI", "Symbol"].str.zfill(6)]
kosdaqCode = [ticker for ticker in tickerData.loc[tickerData["Market"] == "KOSDAQ", "Symbol"].str.zfill(6)]

processor = PreProcessor(kospiTickers=kospiCode, kosdaqTickers=kosdaqCode, startDate="2016-01-01", endDate="2020-12-30",
                         alertData=investAlertData, rollingWindow=15)

processor.concatenatedData.to_csv("./processedDataSet/dataSet.csv")
