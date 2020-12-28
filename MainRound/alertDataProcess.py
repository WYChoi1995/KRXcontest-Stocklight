from datetime import datetime
from enum import IntEnum

from pandas import read_csv

from korToEng import *


class AlertLevel(IntEnum):
    CAUTION = 0
    WARNING = 1
    DANGER = 2


def process_ticker(ticker):
    if len(ticker) <= 6:
        return ticker.zfill(6)

    else:
        return ticker


def process_alert_data(path: str, level: AlertLevel):
    givenData = read_csv(path, encoding='cp949', dtype={IssueCode: str})
    givenData[IssueCode] = givenData[IssueCode].map(lambda ticker: process_ticker(ticker=ticker))

    if level == AlertLevel.CAUTION:
        alertData = givenData[[IssueCode, DesignatedDate]]
        resultDict = {}

        for indexNum, row in alertData.iterrows():
            if row[IssueCode] in resultDict.keys():
                resultDict[row[IssueCode]].append([row[DesignatedDate], row[DesignatedDate]])

            else:
                resultDict[row[IssueCode]] = [[row[DesignatedDate], row[DesignatedDate]]]

    else:
        alertData = givenData[[IssueCode, DesignatedDate, ReleaseDate]]
        todayString = datetime.today().strftime("%Y-%m-%d")
        resultDict = {}

        for indexNum, row in alertData.iterrows():
            if row[IssueCode] in resultDict.keys():
                if row[ReleaseDate] == "-":
                    resultDict[row[IssueCode]].append([row[DesignatedDate], todayString])

                else:
                    resultDict[row[IssueCode]].append([row[DesignatedDate], row[ReleaseDate]])

            else:
                if row[ReleaseDate] == "-":
                    resultDict[row[IssueCode]] = [[row[DesignatedDate], todayString]]

                else:
                    resultDict[row[IssueCode]] = [[row[DesignatedDate], row[ReleaseDate]]]

    return resultDict


investAlertData = {"InvestCaution": process_alert_data("./alertData/investCaution1620.csv", AlertLevel.CAUTION),
                   "InvestWarning": process_alert_data("./alertData/investWarning1620.csv", AlertLevel.WARNING),
                   "InvestDanger": process_alert_data("./alertData/investDanger1620.csv", AlertLevel.DANGER)}
