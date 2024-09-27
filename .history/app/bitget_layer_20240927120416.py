import asyncio
import numpy as np
import pandas as pd
import aiohttp
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Literal

class Granularity:
    MINUTE_1 = '60'
    MINUTE_5 = '300'
    HOUR_1 = '3600'
    HOUR_4 = '14400'
    DAY_1 = '86400'


class BitgetService:
    def __init__(self) -> None:
        self.max_pages = 5

    async def get_historical_funding_rate(self, symbol: str,):
        """
        Return: [[funding_rate, datetime_period, period]] 
        Limit: 500
        """
        final_result = np.empty((0, 3))  

        for page_number in range(1, self.max_pages + 1): 
            url = f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=100&pageNo={page_number}"
            params = {"symbol": symbol, "productType": "USDT-FUTURES"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        if data:
                            page_data = [
                                (
                                    float(fr["fundingRate"]) * 100,  
                                    datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc)  
                                    .astimezone(ZoneInfo('Europe/Amsterdam'))
                                    .isoformat(),
                                    float(fr["fundingTime"]),  
                                )
                                for fr in data
                            ]

                            np_page_data = np.array(page_data, dtype=object)  
                            final_result = np.vstack([final_result, np_page_data])
                    else:
                        print(f"Error fetching funding rate data: {response.status}")
                        return np.array([])  

        return final_result


    async def get_all_cryptos(self):
        url = "https://api.bitget.com/api/v2/mix/market/tickers"
        params = {
            "productType": "USDT-FUTURES"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    cryptos = result.get('data')
                    result = np.array([crypto["symbol"] for crypto in cryptos])

                    return result
                else:
                    response = await response.text()
                    raise ValueError(f"An error ocurred, status {response.status}, whole error: {response}")
                
    async def get_candlestick_chart(self, symbol: str, granularity, start_time: int = None, end_time: int = None) -> np.ndarray:
            final_result = np.empty((0, 7))
            base_url = 'https://api.bitget.com/api/v2/mix/market/candles'
            params = {
                'symbol': symbol,
                'granularity': granularity,
                'productType': 'USDT-FUTURES',
                'limit': 1000
            }

            # Calculate the time difference and number of candles required
            time_diff = end_time - start_time
            granularity_ms = int(granularity) * 1000  # granularity in seconds, convert to milliseconds
            total_candles = time_diff // granularity_ms

            print(f"Total candles needed: {total_candles}")

            if start_time:
                params['startTime'] = str(start_time)
            if end_time:
                params['endTime'] = str(end_time)

            async with aiohttp.ClientSession() as session:
                while True:
                    async with session.get(base_url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            data = result.get("data", [])

                            if not data:
                                break

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

                            # If the last fetched timestamp reaches or exceeds the requested end_time, stop fetching data
                            if end_time and last_timestamp >= end_time:
                                break

                            # Update startTime to last_timestamp + 1 to continue fetching the next 1000 candles
                            params['startTime'] = str(last_timestamp + 1)

                        else:
                            print(f"Error fetching candlestick data: {response.status}")
                            break

            return final_result




    async def get_candlestick_chart_v2(self, symbol):pass

    async def get_crypto_period(self, symbol):
        """Get funding rate period, either 8h or 4h"""
        # STEP 1, get sample data
        url = "https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=3"
        params = {"symbol": symbol, "productType": "USDT-FUTURES"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", [])

                    # Ensure there are at least two records to calculate the difference
                    if len(data) < 2:
                        raise ValueError("Not enough data to determine the funding rate period.")

                    # Convert the timestamps to datetime objects
                    page_data = [
                        datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc) for fr in data
                    ]

                    # Calculate the time difference between the first two records
                    v1 = page_data[0]
                    v2 = page_data[1]
                    difference = v1 - v2

                    # Check if the difference is either 8 hours or 4 hours
                    if difference == timedelta(hours=8):
                        return 8
                    elif difference == timedelta(hours=4):
                        return 4
                    else:
                        raise ValueError(f"Unexpected time difference: {difference}")




async def main_testing():
    start_time = int(datetime(2024, 7, 1).timestamp() * 1000)
    end_time = int(datetime(2024, 9, 10).timestamp() * 1000)

    bitget_layer = BitgetService()

    granularity = '1H'

    res = await bitget_layer.get_candlestick_chart("BTCUSDT", granularity, start_time, end_time)

    df = pd.DataFrame(res, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.to_csv('delete_this.csv', index=False)

    print(df)

if __name__ == "__main__":
    asyncio.run(main_testing())