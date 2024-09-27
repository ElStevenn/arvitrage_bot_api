import asyncio
import numpy as np
import pandas as pd
import aiohttp
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
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

    async def get_historical_funding_rate(self, symbol: str):
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

    async def get_candlestick_chart(self, symbol: str, granularity: str = '1m', start_time: str = None, end_time: str = None) -> np.ndarray:
        final_result = np.empty((0, 7))  
        base_url = 'https://api.bitget.com/api/v2/mix/market/candles'
        params = {
            'symbol': symbol,
            'granularity': granularity,
            'productType': 'USDT-FUTURES',
            'limit': 1000  # The maximum limit
        }

        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        async with aiohttp.ClientSession() as session:
            while True:  # Keep requesting until no more data is available
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        if not data:
                            break  # Stop if there's no more data

                        # Process and convert the data to a NumPy array
                        np_data = np.array([
                            [
                                int(item[0]),  # timestamp in milliseconds
                                float(item[1]),  # open price
                                float(item[2]),  # high price
                                float(item[3]),  # low price
                                float(item[4]),  # close price
                                float(item[5]),  # volume in base currency
                                float(item[6])   # notional value
                            ]
                            for item in data
                        ], dtype=object)

                        # Append the current data to the final result
                        final_result = np.vstack([final_result, np_data])

                        # Update the start_time to continue from the last timestamp
                        last_timestamp = data[-1][0]
                        params['startTime'] = str(int(last_timestamp) + 1)
                    else:
                        print(f"Error fetching candlestick data: {response.status}")
                        break

        return final_result



async def main_testing():
    for page_number in [page * 100 for page in range(5)]:
        print(page_number)
    
    bitget_layer = BitgetService()

    res = await bitget_layer.get_candlestick_chart("BTCUSDT", '1m')

    print(res)
    

if __name__ == "__main__":
    asyncio.run(main_testing())