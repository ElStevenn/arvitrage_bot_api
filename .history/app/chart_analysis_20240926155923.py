from app.bitget_layer import BitgetService


class FundingRateChart:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bitget_service = BitgetService()
        self.df = None
    

    def 