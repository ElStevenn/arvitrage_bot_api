from app.bitget_layer import BitgetService, Granularity
import pandas as pd
import numpy as np

class FundingRateChart:
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.bitget_service = BitgetService()
        self.df = None
    

    async def set_analysis(self, perdiod: int) -> dict:
        """
            period: when funding rate was over
            Call this function if funding rate was higer than 0.5
            Response:
            {
                "description": List[],  
                "period": str,
                "8h_variation": float,
                "10m_variation": float,
                "dialy_trend": Literal[ "bullish", "bearish", "neutral", "highly bullish", "highly bearish", "volatile", "sideways", "corrective", "strongly bullish", "strongly bearish" ],
                "weekly_trend": Literl[ "bullish", "bearish", "neutral", "highly bullish", "highly bearish", "volatile", "sideways", "corrective", "strongly bullish", "strongly bearish" ],
                "volatility_index": float
                "average_trading_volume": int
                "market_sentiment": Literal[ "positive", "negative", "neutral", "highly positive", "highly negative", "mixed", "uncertain", "fearful", "optimistic", "pessimistic", "bullish", "bearish" ]
            }
        """


        result = {


        }

        return result
    
    async def get_8h_variation(self, period: int):
        """Get variation since funding rate was up until 8 hours later"""
        granularity = '5min'



        self.bitget_service.get_candlestick_chart(self.symbol, granularity, start_time=period)

        
    
    async def get_10m_variation(self, period: int):
        granularity = '1min'
        pass



        