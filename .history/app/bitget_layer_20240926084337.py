import asyncio
import numpy as np
import pandas as pd
import aiohttp
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from zoneinfo import ZoneInfo



class BitgetService:
    def __init__(self) -> None:
        self.max_pages = 500

    async def get_historical_funding_rate(self, symbol: str):
        final_result = np.array([])
        
        for page in range(5):
        url = f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=100"
        params = {"symbol": symbol, "productType": "USDT-FUTURES"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        # Define a unique dtype for the structured array
                        dtype = [
                            ('fundingRateTimes100', 'float32'),  
                            ('fundingTimeEurope', 'U25'),
                            ('fundingTimeDefault', 'float32')  
                        ]
                        
                        # Convert the fetched data to a NumPy structured array
                        np_data = np.array([
                            (
                                float(fr["fundingRate"]) * 100,  # Funding rate times 100
                                datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc)  # Funding time as ISO string format
                                .astimezone(ZoneInfo('Europe/Amsterdam'))
                                .isoformat(),
                                float(fr["fundingTime"]),  # Funding time in default format
                            )
                            for fr in data
                        ], dtype=dtype)
                        
                        # Convert NumPy array to list of Python native types for serialization
                        return jsonable_encoder(np_data.tolist())
                    else:
                        print(f"Error fetching funding rate data: {response.status}")
                        return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
 
        



async def main_testing():
    bitget_layer = BitgetService()

    res = await bitget_layer.get_historical_funding_rate("DOGUSDT")
    print(res)

if __name__ == "__main__":
    asyncio.run(main_testing())