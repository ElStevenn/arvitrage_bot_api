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

    def convert_granularity_to_ms(self, granularity: str) -> int:
            mapping_ms = {
                "1m": 60 * 1000,
                "5m": 5 * 60 * 1000,
                "15m": 15 * 60 * 1000,
                "30m": 30 * 60 * 1000,
                "1H": 3600 * 1000,
                "4H": 4 * 3600 * 1000,
                "12H": 12 * 3600 * 1000,
                "1D": 24 * 3600 * 1000,
                "1W": 7 * 24 * 3600 * 1000,
                "1MO": 30 * 24 * 3600 * 1000
            }
            if granularity in mapping_ms:
                return mapping_ms[granularity]
            else:
                raise ValueError(f"Unsupported granularity: {granularity}")

    def convert_granularity_to_api_format(self, granularity: str) -> str:
        mapping = {
            "1m": "60",
            "5m": "300",
            "15m": "900",
            "30m": "1800",
            "1H": "3600",
            "4H": "14400",
            "12H": "43200",
            "1D": "86400",
            "1W": "604800",
            "1MO": "2592000"
        }
        if granularity in mapping:
            return mapping[granularity]
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")

    async def get_candlestick_chart(self, symbol: str, granularity: str, start_time: int = None, end_time: int = None) -> np.ndarray:
        final_result = []
        base_url = 'https://api.bitget.com/api/v2/mix/market/candles'

        # Convert granularity to the format required by the API
        api_granularity = self.convert_granularity_to_api_format(granularity)

        params = {
            'symbol': symbol,
            'granularity': api_granularity,  # Use the converted granularity
            'productType': 'USDT-FUTURES',
            'limit': 1000
        }

        granularity_ms = self.convert_granularity_to_ms(granularity)

        if end_time is None:
            end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

        if start_time is None:
            start_time = end_time - granularity_ms * 1000  # Default to fetch the last 1000 data points

        if start_time >= end_time:
            raise ValueError("start_time must be less than end_time")

        async with aiohttp.ClientSession() as session:
            while True:
                params['startTime'] = str(start_time)
                params['endTime'] = str(end_time)

                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        if not data:
                            print("No more data available.")
                            break

                        # Data is returned in reverse chronological order (newest first)
                        # We reverse it to chronological order
                        data_reversed = data[::-1]

                        for item in data_reversed:
                            timestamp = int(item[0])

                            if timestamp < start_time or timestamp > end_time:
                                continue

                            final_result.append([
                                timestamp,
                                float(item[1]),  # Open price
                                float(item[2]),  # High price
                                float(item[3]),  # Low price
                                float(item[4]),  # Close price
                                float(item[5]),  # Volume
                                float(item[6])   # Notional value
                            ])

                        earliest_timestamp = int(data_reversed[0][0])
                        new_end_time = earliest_timestamp - granularity_ms

                        if new_end_time <= start_time or new_end_time >= end_time:
                            break

                        end_time = new_end_time

                    else:
                        response_text = await response.text()
                        print(f"Error fetching candlestick data: {response.status}, {response_text}")
                        break

        if not final_result:
            print("No data was fetched. Please check the parameters.")
            return np.array([])

        np_final_result = np.array(final_result, dtype=object)
        return np_final_result







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
    start_time = int(datetime(2023, 7, 1).timestamp() * 1000)
    end_time = int(datetime(2023, 9, 10).timestamp() * 1000)

    bitget_layer = BitgetService()

    res = await bitget_layer.get_candlestick_chart("BTCUSDT", '1H', start_time, end_time)

    df = pd.DataFrame(res, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.to_csv('candlestick_data.csv', index=False)

    print(df)

if __name__ == "__main__":
    asyncio.run(main_testing())
