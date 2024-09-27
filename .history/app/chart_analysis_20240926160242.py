from app.bitget_layer import BitgetService


class FundingRateChart:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bitget_service = BitgetService()
        self.df = None
    

    def set_analysis(self) -> str:
        """
            Call this function if funding rate was higer than 0.5
            Response:
            {
                "description": List[],  
                ""
                ""
                ""
                ""
                ""
            
            }
        """



        return object