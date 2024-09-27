import matplotlib.pyplot as plt
from datetime import datetime, timezone
import numpy as np
import asyncio

from app.bitget_layer import BitgetService

bitget_service = BitgetService()



start_time = int(datetime(2024, 9, 1, 1).timestamp() * 1000)  
end_time = int(datetime(2024, 9, 8).timestamp() * 1000)  

granularity = '1m'


async def make_chart():
    numpy_data  = await bitget_service.get_candlestick_chart('BTCUSDT', granularity, start_time, end_time)


asyncio.run(make_chart())