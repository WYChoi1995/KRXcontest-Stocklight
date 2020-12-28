class InvestAlertModel(object):
    def __init__(self, tickers, trainSet: dict, testSet: dict):
        self.tickers = tickers
        self.trainSet = trainSet
        self.testSet = testSet
