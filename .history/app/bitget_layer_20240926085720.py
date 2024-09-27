import asyncio
import numpy as np
import pandas as pd
import aiohttp
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from zoneinfo import ZoneInfo



class BitgetService:
    def __init__(self) -> None:
        self.max_pages = 5

    async def get_historical_funding_rate(self, symbol: str):
        final_result = np.empty((0, 3))  

        for page_number in range(1, self.max_pages + 1): 
            url = f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=100&pageNo={page_number}"
            params = {"symbol": symbol, "productType": "USDT-FUTURES"}

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            data = result.get("data", [])

                            # Create a list of tuples for the current page
                            page_data = [
                                (
                                    float(fr["fundingRate"]) * 100,  # Funding rate times 100
                                    datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc)  # Funding time in Europe/Amsterdam
                                    .astimezone(ZoneInfo('Europe/Amsterdam'))
                                    .isoformat(),
                                    float(fr["fundingTime"]),  # Funding time in default format
                                )
                                for fr in data
                            ]

                            # Convert the page data to a NumPy array
                            np_page_data = np.array(page_data, dtype=object)  # Use dtype=object to handle mixed types
                            
                            # Append the page data to the final result
                            final_result = np.vstack([final_result, np_page_data])  # Stack vertically to maintain 2D structure
                        else:
                            print(f"Error fetching funding rate data: {response.status}")
                            return np.array([])  # Return empty array in case of an error
            except Exception as e:
                print(f"An error occurred: {e}")
                return np.array([])  # Return empty array in case of an exception

        return final_result  # Return the 2D array




async def main_testing():
    for page_number in [page * 100 for page in range(5)]:
        print(page_number)
    
    bitget_layer = BitgetService()

    res = await bitget_layer.get_historical_funding_rate("DOGUSDT")

    print(res)
    print("lenght", len(res))

if __name__ == "__main__":
    asyncio.run(main_testing())