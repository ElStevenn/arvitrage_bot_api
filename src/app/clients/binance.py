import asyncio
import numpy as np
import aiohttp, pytz
from src.app.proxy import APIProxy
from datetime import datetime

class BinanceClient(APIProxy):
    def __init__(self):
        super().__init__()
        self.binance_url = "https://fapi.binance.com"

    def convert_interval_to_ms(self, interval: str) -> int:
        mapping = {
            '1m': 60 * 1000,
            '3m': 3 * 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '2h': 2 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '8h': 8 * 60 * 60 * 1000,
            '12h': 12 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '3d': 3 * 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
            '1M': 30 * 24 * 60 * 60 * 1000
        }
        return mapping.get(interval, 60 * 60 * 1000)  # Default to 1h

    async def get_candlestick_chart(
        self,
        symbol: str,
        interval: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = 1000
    ) -> np.ndarray:
        final_result = np.empty((0, 6))
        url = f"{self.binance_url}/fapi/v1/klines"
        granularity_ms = self.convert_interval_to_ms(interval)
        
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = int(datetime.utcnow().timestamp() * 1000)
        
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time,
                    "limit": limit
                }
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print(f"Error fetching candlestick data: {response.status}")
                        break
                    data = await response.json()
                    if not data:
                        break
                    np_data = np.array([
                        [
                            int(item[0]),
                            float(item[1]),
                            float(item[2]),
                            float(item[3]),
                            float(item[4]),
                            float(item[5])
                        ]
                        for item in data
                    ], dtype=object)
                    final_result = np.vstack([final_result, np_data])
                    last_timestamp = int(data[-1][0])
                    if last_timestamp >= end_time:
                        break
                    start_time = last_timestamp + granularity_ms
        return final_result

    async def get_historical_funding_rate(self, symbol, limit=20, fromId=None):
        url = f"{self.binance_url}/fapi/v1/fundingRate"
        params = {"symbol": symbol, "limit": limit}
        if fromId is not None:
            params["fromId"] = fromId
        return await self.curl_api(url, method='GET', body=params)

    async def get_last_contract_funding_rate(self, symbol):
        """Get the last funding rate in a readable format."""
        data = await self.get_historical_funding_rate(symbol, limit=1)
        if data and isinstance(data, list):
            raw_rate = float(data[0].get('fundingRate', 0))
            # Convert to a readable number
            readable_rate = round(raw_rate, 8)  
            # Ensure proper string formatting for printing
            formatted_rate = f"{readable_rate:.8f}"  
            return formatted_rate
        return None


    async def get_all_future_tickers(self) -> np.ndarray:
        url = self.binance_url + "/fapi/v1/ticker/price"
        data = await self.curl_api(url, method='GET')
        if data and isinstance(data, list):
            return np.array([ticker.get('symbol') for ticker in data])
        return np.array([])

    async def get_ticker(self, symbol):
        url = self.binance_url + "/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        data = await self.curl_api(url, method='GET', body=params)
        if data and isinstance(data, list):
            return data[0]
        return None

    async def get_account_information(self):
        url = f"{self.binance_url}/fapi/v2/account"
        return await self.curl_api(url, method='GET', authenticated=True)

    async def close_client(self):
        await super().close_client()

    # DEPRECIATED FUNCTION
    async def get_price_of_period(self, symbol: str, period: int):
        """Get what was the price from a given symbol (in Opening time)"""
        
        end_time = period + (1 * 60 * 1000)
        period_ = await self.get_candlestick_chart(symbol, '1m', period, end_time)

        if period_.size > 0:
            return period_[0][4]
        else:
            timestamp = datetime.fromtimestamp(int(period) / 1000, pytz.timezone('Europe/Amsterdam'))
            raise ValueError(f"Period {timestamp} doesn't exist")
    

async def main_testing():
    binance_client = BinanceClient()
    start_time = int(datetime.now().timestamp() * 1000) - (5 * 60 * 1000)  
    end_time = int(datetime.now().timestamp() * 1000)

    try:


        # future_tickers = await binance_client.get_all_future_tickers()
        # print(f"Sample Tickers: {future_tickers[:10]}")
        # ticker = await binance_client.get_ticker("BTCUSDT"); print(f"Ticker: {ticker}")
        last_fr = await binance_client.get_last_contract_funding_rate("MEUSDT"); print(f"Last Funding Rate: {last_fr}")
        
        # candlestick_data = await binance_client.get_candlestick_chart(
        #     symbol="BTCUSDT",
        #     interval="1h",
        #     start_time=1633046400000,  # Example: 2021-10-01 00:00:00 UTC
        #     end_time=1635724800000     # Example: 2021-11-01 00:00:00 UTC
        # )
        # print(f"Candlestick Data Shape: {candlestick_data.shape}")
        # print(f"First 5 Candlesticks:\n{candlestick_data[:5]}")
        
    except Exception as e:
        print(f"Failed during main testing: {e}")
    finally:
        await binance_client.close_client()

if __name__ == "__main__":
    asyncio.run(main_testing())
