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
        # Get Candlestick data
        granularity = '1H'
        end_time = period + 8 * 60 * 60 * 1000
        candle_stick_data = self.bitget_service.get_candlestick_chart(self.symbol, granularity, start_time=period, end_time=end_time)

        if not candle_stick_data:
            candle_stick_data = self.bitget_service.get_candlestick_chart(self.symbol, '4H', start_time=period, end_time=end_time)
            if not candle_stick_data:
                raise Exception("The chart is not avariable, so i think i shouldn't be possible to access")
        
        df = pd.DataFrame()

        # Calculate variation


    
    async def get_10m_variation(self, period: int):
        granularity = '1min'
        pass



        