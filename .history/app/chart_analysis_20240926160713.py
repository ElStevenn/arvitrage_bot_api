from app.bitget_layer import BitgetService


class FundingRateChart:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bitget_service = BitgetService()
        self.df = None
    

    def set_analysis(self, perdiod) -> str:
        """
            period: when funding rate was over
            Call this function if funding rate was higer than 0.5
            Response:
            {
                "description": List[],  
                "period": str
                "8h_variation": float
                "10m_variation": float
                "dialy_trend": Literal['']
                "weekly_trend": Literl
            
            }
        """



        return object