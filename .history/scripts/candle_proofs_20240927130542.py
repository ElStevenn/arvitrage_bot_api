import matplotlib.pyplot as plt
from datetime import datetime, timezone
import numpy as np

from app.bitget_layer import BitgetService

bitget_service = BitgetService()



start_time = int(datetime(2024, 9, 1, 1).timestamp() * 1000)  
end_time = int(datetime(2024, 9, 8).timestamp() * 1000)  

granularity = '1m'

numpy_data = res = await bitget_layer.get_candlestick_chart('BTCUSDT', granularity, start_time, end_time)

