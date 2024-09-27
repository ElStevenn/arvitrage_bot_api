import asyncio
import numpy as np
import pandas as pd
import aiohttp
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Literal

Granularity = Literal[
    '1min', '5min', '15min', '30min', 
    '1h', '4h', '6h', '12h',          
    '1day', '3day',                   
    '1week',                           
    '1M',                             
    '6Hutc', '12Hutc', '1Dutc', '3Dutc', '1Wutc', '1Mutc' 
]


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

    async def get_candlestick_chart(self, symbol: str, granularity: Granularity, start_time: str = None, end_time: str = None) -> np.ndarray:
        final_result = np.empty((0, 7))  
        base_url = 'https://api.bitget.com/api/v2/mix/market/candles'
        params = {
            'symbol': symbol,
            'granularity': granularity,
            'productType': 'USDT-FUTURES',
            'limit': 1000  # Maximum limit per API request
        }

        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        if not data:
                            break  # Exit loop if there's no more data

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

                        # Update startTime for the next request
                        last_timestamp = data[-1][0]
                        params['startTime'] = str(int(last_timestamp) + 1)  # Increment timestamp for pagination
                    else:
                        print(f"Error fetching candlestick data: {response.status}")
                        break

        return final_result


    async def get_candlestick_chart_v2(self):pass

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
    for page_number in [page * 100 for page in range(5)]:
        print(page_number)
    
    bitget_layer = BitgetService()

    res = await bitget_layer.get_candlestick_chart("BTCUSDT")

    print(res)
    

if __name__ == "__main__":
    asyncio.run(main_testing())