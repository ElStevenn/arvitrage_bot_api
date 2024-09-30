from app.bitget_layer import BitgetService, Granularity
from datetime import datetime
import pandas as pd
import numpy as np
import asyncio

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
        candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, granularity, start_time=period, end_time=end_time)

        if not candle_stick_data.any():
            candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, '4H', start_time=period, end_time=end_time)
            if not candle_stick_data.any():
                raise Exception("The chart is not avariable, so i think i shouldn't be possible to access")
        
        df = pd.DataFrame(candle_stick_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])

        print(df)

        # Calculate variation
        start_price = df['open'].iloc[0]
        end_price = df['close'].iloc[-1]
        
        volatility = ((start_price - end_price) / end_price) * 100    
    
        return volatility

    async def get_10m_variation(self, period: int):
        granularity = '1m'
        end_time = period + 10 * 60 * 1000
        candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, granularity, start_time=period, end_time=end_time)

        if not candle_stick_data.any():
            candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, '4H', start_time=period, end_time=end_time)
            if not candle_stick_data.any():
                raise Exception("The chart is not avariable, so i think i shouldn't be possible to access")
        
        df = pd.DataFrame(candle_stick_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])

        # Calculate variation
        start_price = df['open'].iloc[0]
        # end_price = df['close'].iloc[-1]
        lowest_price = df['low'].min()

        volatility = ((start_price - lowest_price) / lowest_price) 
        return volatility


    async def get_dialy_trend(self, ):
        today = (datetime.today().timestamp() * 1000)

        


async def main_testing():
    chart_analysis = FundingRateChart("DOGUSDT")
    period = int(datetime(2024, 9, 29).timestamp() * 1000)

    res = await chart_analysis.get_10m_variation(period)
    print(res)


if __name__ == "__main__":
    asyncio.run(main_testing())