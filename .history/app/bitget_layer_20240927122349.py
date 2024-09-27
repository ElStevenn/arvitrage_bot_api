import asyncio
import numpy as np
import pandas as pd
import aiohttp
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

class BitgetService:
    def __init__(self) -> None:
        self.max_pages = 5

    # Other methods remain unchanged...

    def convert_granularity_to_ms(self, granularity: str) -> int:
        mapping_ms = {
            "1m": 60 * 1000,
            "3m": 3 * 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1H": 3600 * 1000,
            "4H": 4 * 3600 * 1000,
            "6H": 6 * 3600 * 1000,
            "12H": 12 * 3600 * 1000,
            "1D": 24 * 3600 * 1000,
            "3D": 3 * 24 * 3600 * 1000,
            "1W": 7 * 24 * 3600 * 1000,
            "1M": 30 * 24 * 3600 * 1000,
            # Include UTC variants if needed
        }
        if granularity in mapping_ms:
            return mapping_ms[granularity]
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")

    def align_timestamp(self, timestamp: int, granularity_ms: int) -> int:
        return timestamp - (timestamp % granularity_ms)

    async def get_candlestick_chart(self, symbol: str, granularity: str, start_time: int = None, end_time: int = None) -> np.ndarray:
        final_result = []
        base_url = 'https://api.bitget.com/api/v2/mix/market/candles'

        # Use granularity as per API documentation
        params = {
            'symbol': symbol,
            'granularity': granularity,
            'productType': 'USDT-FUTURES',
            'limit': 1000
        }

        granularity_ms = self.convert_granularity_to_ms(granularity)

        if end_time is None:
            end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

        if start_time is None:
            start_time = end_time - granularity_ms * 1000  # Default to fetch the last 1000 data points

        # Align start_time and end_time to granularity
        start_time = self.align_timestamp(start_time, granularity_ms)
        end_time = self.align_timestamp(end_time, granularity_ms)

        if start_time >= end_time:
            raise ValueError("start_time must be less than end_time")

        # Check maximum query range based on granularity
        max_days = {
            "1m": 31,
            "3m": 31,
            "5m": 31,
            "15m": 52,
            "30m": 62,
            "1H": 83,
            "2H": 120,
            "4H": 240,
            "6H": 360,
            "12H": 360,
            "1D": 360,
            "3D": 360,
            "1W": 360,
            "1M": 360,
        }

        if granularity in max_days:
            max_range_ms = max_days[granularity] * 24 * 3600 * 1000
            if (end_time - start_time) > max_range_ms:
                print(f"Reducing date range to the maximum allowed for granularity '{granularity}'.")
                start_time = end_time - max_range_ms

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

    # Other methods remain unchanged...

async def main_testing():
    # Ensure that the dates are within the maximum allowed by the API for the given granularity
    # For '1H' granularity, maximum is 83 days
    end_time = int(datetime(2023, 9, 10, tzinfo=timezone.utc).timestamp() * 1000)
    start_time = end_time - 83 * 24 * 3600 * 1000  # 83 days in milliseconds

    bitget_layer = BitgetService()

    res = await bitget_layer.get_candlestick_chart("BTCUSDT", '1H', start_time, end_time)

    if res.size == 0:
        print("No data was returned from get_candlestick_chart.")
        return

    df = pd.DataFrame(res, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'notional'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.to_csv('candlestick_data.csv', index=False)

    print(df)

if __name__ == "__main__":
    asyncio.run(main_testing())
