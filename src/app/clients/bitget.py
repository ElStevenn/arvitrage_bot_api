import asyncio
import time, pytz
import numpy as np
import aiohttp
from datetime import datetime, timedelta
from typing import Literal

from src.app.proxy import APIProxy

class BitgetClient(APIProxy):
    def __init__(self):
        super().__init__()
        self.bitget_url = "https://api.bitget.com"

    async def get_historical_funding_rate(self, symbol, limit=20, offset=0):
        """Get historical funding rate from a given symbol"""
        url = self.bitget_url +  "/api/v2/mix/market/history-fund-rate"
        params = {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "pageSize": limit,
            "pageNo": offset + 1
        }
        data = await self.curl_api(url, method='GET', body=params)
        return data

    async def get_last_contract_funding_rate(self, symbol):
        """Get the last contract funding rate"""
        data = await self.get_historical_funding_rate(symbol)
        return data.get('data', None)[0]['fundingRate']
        
    async def get_tiker(self, symbol):
        url = self.bitget_url + "/api/v2/mix/market/ticker"
        params = {
            "symbol": symbol,
            "productType": "USDT-FUTURES"
        }
        data = await self.curl_api(url, method='GET', body=params)
        return data.get('data', None)[0] if data else None

    
    async def get_all_future_tikers(self) -> np.ndarray:
        """Get all the available symbols in the futures market"""
        url = self.bitget_url  + "/api/v2/mix/market/tickers"
        params = {
            "productType": "USDT-FUTURES"
        }
        data = await self.curl_api(url, method='GET', body=params)
        # print(data)  # Optional: Remove or comment out in production
        future_tikers = data.get("data", [])

        return np.array([tiker.get('symbol') for tiker in future_tikers])

    def convert_granularity_to_ms(self, granularity: int) -> int:
        return granularity * 1000

    def calculate_api_calls(self, start_time: int, end_time: int, granularity_ms: int, page_size: int = 1000):
        total_candles = (end_time - start_time) // granularity_ms
        api_calls = []
        for i in range(0, total_candles, page_size):
            call_start = start_time + i * granularity_ms
            call_end = min(call_start + page_size * granularity_ms, end_time)
            api_calls.append({'start_time': call_start, 'end_time': call_end})
        return api_calls

    async def get_candlestick_data(
        self,
        symbol: str = "BTCUSDT_UMCBL",  # Example symbol
        granularity: Literal['1m', '3m', '5m', '15m', '30m', '1H', '4H', '6H', '12H', '1D', '3D', '1W', '1M'] = '1H',
        product_type: str = "umcbl",
        start_time: int = None,
        end_time: int = None,
        page_size: int = 1000
    ) -> np.ndarray:
        final_result = np.empty((0, 7))
        base_url = self.bitget_url + "/api/mix/v1/market/candles"
        granularity_ms = self.convert_granularity_to_ms(granularity)

        if end_time is None:
            end_time = int(time.time() * 1000)
        if start_time is None:
            # Default to last 24 hours if start_time not provided
            start_time = end_time - (24 * 60 * 60 * 1000)

        api_calls = self.calculate_api_calls(start_time, end_time, granularity_ms, page_size)

        async with aiohttp.ClientSession() as session:
            for i, call in enumerate(api_calls):
                params = {
                    "symbol": symbol,
                    "productType": product_type,
                    "granularity": granularity,
                    "startTime": str(call['start_time']),
                    "endTime": str(call['end_time']),
                    "pageSize": str(page_size)
                }

                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        print(f"Error fetching candlestick data: {response.status}")
                        error_text = await response.text()
                        print("Response:", error_text)
                        break

                    data = await response.json()

                    if not data:
                        print(f"No data returned in attempt {i}")
                        break

                    # Data format: [timestamp, open, high, low, close, volume, quoteVolume]
                    np_data = np.array([
                        [
                                    int(item[0]),    # The timestamp in milliseconds
                                    float(item[1]),  # Open price
                                    float(item[2]),  # High price
                                    float(item[3]),  # Low price
                                    float(item[4]),  # Close price
                                    float(item[5]),  # Volume (traded amount in the base currency)
                                    float(item[6])   # Notional value (the total traded value in quote currency)
                        ]
                        for item in data
                    ], dtype=object)

                    final_result = np.vstack([final_result, np_data])
                    last_timestamp = int(data[-1][0])
                    if last_timestamp >= end_time:
                        break

        return final_result
    
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
    bitget_client = BitgetClient()

    # Use a more recent time range. For example, the last 12 hours:
    now_ms = int(time.time() * 1000)
    twelve_hours_ago_ms = now_ms - (12 * 60 * 60 * 1000)

    # Use the correct symbol and productType for Bitget USDT-margined futures:
    symbol = "BTCUSDT_UMCBL"
    granularity = 3600  # 1 hour
    try:
        candlestick_data = await bitget_client.get_candlestick_data(
            symbol=symbol,
            granularity=granularity,
            start_time=twelve_hours_ago_ms,
            end_time=now_ms,
            page_size=500
        )
        print(f"Candlestick Data Shape: {candlestick_data.shape}")
        print(f"First 5 Candlesticks:\n{candlestick_data[:5]}")

    except Exception as e:
        print(f"Failed during main testing: {e}")
    finally:
        await bitget_client.close_client()

if __name__ == "__main__":
    asyncio.run(main_testing())
