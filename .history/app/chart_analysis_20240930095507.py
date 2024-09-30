from app.bitget_layer import BitgetService, Granularity
from datetime import datetime, timezone
from typing import Literal
import pandas as pd
import numpy as np
import asyncio

class FundingRateChart:
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.bitget_service = BitgetService()
        self.df8h = None
        self.df10m = None
        self.dfweekly = None

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

        h8_variation = await self.get_8h_variation(perdiod)
        h10m_variation = await self.get_10m_variation(perdiod)
        daily_trend = await self.get_daily_trend(perdiod)
        weekly_trend = await self.get_weekly_trends(perdiod)
        volatility_index = await self.get_volatility_index()

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
        
        self.df8h = pd.DataFrame(candle_stick_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])

        print(self.df8h)

        # Calculate variation
        start_price = self.df8h['open'].iloc[0]
        regression = self.df8h['low'].min()
        end_price = self.df8h['close'].iloc[-1]
        
        volatility = ((start_price - end_price) / end_price) * 100    
        regg = ((start_price - regression) / regression) * 100

        return volatility

    async def get_10m_variation(self, period: int):
        granularity = '1m'
        end_time = period + 10 * 60 * 1000
        candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, granularity, start_time=period, end_time=end_time)

        if not candle_stick_data.any():
            candle_stick_data = await self.bitget_service.get_candlestick_chart(self.symbol, '4H', start_time=period, end_time=end_time)
            if not candle_stick_data.any():
                raise Exception("The chart is not avariable, so i think i shouldn't be possible to access")
        
        self.df10m = pd.DataFrame(candle_stick_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])
        
        # Calculate variation
        start_price = self.df10m['open'].iloc[0]
        # end_price = df['close'].iloc[-1]
        lowest_price = self.df10m['low'].min()

        volatility = ((start_price - lowest_price) / lowest_price) 
        return volatility


    async def get_daily_trend(self, period: int) -> Literal[
            "bullish", "bearish", "neutral", "highly bullish", "highly bearish",
            "volatile", "sideways", "corrective", "strongly bullish", "strongly bearish"
        ]:
            """
            Analyze the daily trend based on candlestick data and return a trend descriptor.
            """
            # Define the time range for one day
            start_time = period
            end_time = period + 24 * 60 * 60 * 1000  

            # Fetch candlestick data for the day at 15-minute intervals
            granularity = '15m'
            candle_stick_data = await self.bitget_service.get_candlestick_chart(
                self.symbol, granularity, start_time=start_time, end_time=end_time
            )

            if not candle_stick_data.any():
                raise Exception("The chart data is not available for the specified period.")

            # Create DataFrame
            df_daily = pd.DataFrame(candle_stick_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'
            ])

            # Ensure numeric data types
            for col in ['open', 'high', 'low', 'close', 'volume', 'notional']:
                df_daily[col] = pd.to_numeric(df_daily[col])

            # Calculate price changes
            df_daily['price_change'] = df_daily['close'].diff()
            df_daily['price_change_pct'] = df_daily['close'].pct_change() * 100

            # Calculate moving averages
            df_daily['ma20'] = df_daily['close'].rolling(window=20).mean()
            df_daily['ma50'] = df_daily['close'].rolling(window=50).mean()

            # Calculate volatility (standard deviation of price changes)
            volatility = df_daily['price_change_pct'].std()

            # Determine trend based on moving averages
            latest_close = df_daily['close'].iloc[-1]
            latest_ma20 = df_daily['ma20'].iloc[-1]
            latest_ma50 = df_daily['ma50'].iloc[-1]

            # Initialize trend
            trend = "neutral"

            # Define thresholds
            volatility_threshold = 1.5  # You can adjust this value based on asset volatility

            # Analyze trend
            if latest_close > latest_ma20 > latest_ma50:
                trend = "strongly bullish"
            elif latest_close < latest_ma20 < latest_ma50:
                trend = "strongly bearish"
            elif latest_close > latest_ma20:
                trend = "bullish"
            elif latest_close < latest_ma20:
                trend = "bearish"

            # Check for sideways movement
            if abs(latest_ma20 - latest_ma50) / latest_ma50 < 0.01:
                trend = "sideways"

            # Adjust for volatility
            if volatility > volatility_threshold:
                trend = "volatile"

            # Return the determined trend
            return trend


    async def get_weekly_trends(self, period: int) -> Literal[
            "bullish", "bearish", "neutral", "highly bullish", "highly bearish",
            "volatile", "sideways", "corrective", "strongly bullish", "strongly bearish"
        ]:
            """
            Analyze the weekly trend based on candlestick data and return a trend descriptor.
            """
            # Define the time range for one week (7 days)
            start_time = period
            end_time = period + 7 * 24 * 60 * 60 * 1000  # Add 7 days in milliseconds

            # Fetch candlestick data for the week at hourly intervals
            granularity = '1H'  # 1-hour intervals
            candle_stick_data = await self.bitget_service.get_candlestick_chart(
                self.symbol, granularity, start_time=start_time, end_time=end_time
            )

            if not candle_stick_data.any():
                raise Exception("The chart data is not available for the specified period.")

            # Create DataFrame
            self.dfweekly = pd.DataFrame(candle_stick_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'
            ])

            # Ensure numeric data types
            for col in ['open', 'high', 'low', 'close', 'volume', 'notional']:
                self.dfweekly[col] = pd.to_numeric(self.dfweekly[col])

            # Convert timestamp to datetime
            self.dfweekly['datetime'] = pd.to_datetime(self.dfweekly['timestamp'], unit='ms')

            # Calculate price changes
            self.dfweekly['price_change'] = self.dfweekly['close'].diff()
            self.dfweekly['price_change_pct'] = self.dfweekly['close'].pct_change() * 100

            # Calculate moving averages
            self.dfweekly['ma20'] = self.dfweekly['close'].rolling(window=20).mean()
            self.dfweekly['ma50'] = self.dfweekly['close'].rolling(window=50).mean()

            # Calculate volatility (standard deviation of price changes)
            volatility = self.dfweekly['price_change_pct'].std()

            # Determine trend based on moving averages
            latest_close = self.dfweekly['close'].iloc[-1]
            latest_ma20 = self.dfweekly['ma20'].iloc[-1]
            latest_ma50 = self.dfweekly['ma50'].iloc[-1]

            # Initialize trend
            trend = "neutral"

            # Define thresholds
            volatility_threshold = 2.0  # Adjust based on asset volatility
            price_change_threshold = 5.0  # Percentage change threshold for strong trends

            # Calculate total percentage change over the week
            weekly_change_pct = ((latest_close - self.dfweekly['open'].iloc[0]) / df_weekly['open'].iloc[0]) * 100

            # Analyze trend based on moving averages and price changes
            if latest_close > latest_ma20 > latest_ma50:
                if weekly_change_pct > price_change_threshold:
                    trend = "strongly bullish"
                else:
                    trend = "bullish"
            elif latest_close < latest_ma20 < latest_ma50:
                if weekly_change_pct < -price_change_threshold:
                    trend = "strongly bearish"
                else:
                    trend = "bearish"
            elif abs(weekly_change_pct) < 1.0:
                trend = "neutral"
            else:
                # Check for corrective or sideways movement
                if abs(latest_ma20 - latest_ma50) / latest_ma50 < 0.01:
                    trend = "sideways"
                elif weekly_change_pct > 0:
                    trend = "corrective"
                else:
                    trend = "volatile"

            # Adjust for high volatility
            if volatility > volatility_threshold:
                trend = "volatile"

            # Return the determined trend
            return trend

    async def get_volatility_index(self) -> float:
        """
        Calculate the volatility index based on the closing prices in the DataFrame.
        Returns:
            volatility_index (float): The volatility index as a percentage.
        """
        # Ensure that the DataFrame is available
        if self.df10m is None:
            raise ValueError("DataFrame is empty. Please fetch data before calculating volatility.")

        # Ensure numeric data types
        self.df10m['close'] = pd.to_numeric(self.df10m['close'], errors='coerce')

        # Drop any rows with NaN values in 'close'
        self.df10m = self.df10m.dropna(subset=['close'])

        # Calculate log returns
        self.df10m['log_return'] = np.log(self.df10m['close'] / self.df10m['close'].shift(1))

        # Drop the first row which will have NaN log_return
        self.df10m = self.df10m.dropna(subset=['log_return'])

        # Calculate the standard deviation of log returns
        volatility = self.df10m['log_return'].std()

        # Since the data is in minutes and over a short period, we can annualize the volatility
        # For 10-minute data, assuming 1440 minutes per day and 252 trading days per year
        periods_per_year = 252 * (1440 / 10)

        # Annualize the volatility
        annualized_volatility = volatility * np.sqrt(periods_per_year)

        # Convert volatility to percentage
        volatility_index = annualized_volatility * 100

        return volatility_index

    async def set_description(self, regression_8h, volatility_10m, dialy_trend, weekly_tend):
        pass

    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        average_gain = gain.rolling(window=period).mean()
        average_loss = loss.rolling(window=period).mean()
        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    

async def main_testing():
    chart_analysis = FundingRateChart("DOGUSDT")
    period = int(datetime(2024, 9, 29).timestamp() * 1000)
    
    # Fetch data required for df10m
    await chart_analysis.get_10m_variation(period)
    
    volatility_index = await chart_analysis.get_volatility_index()
    print(f"The volatility index is: {volatility_index:.2f}%")

if __name__ == "__main__":
    asyncio.run(main_testing())


if __name__ == "__main__":
    asyncio.run(main_testing())