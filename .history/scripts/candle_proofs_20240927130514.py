import matplotlib.pyplot as plt
from datetime import datetime, timezone
import numpy as np

from app.bitget_layer import BitgetService

bitget_service = BitgetService()



start_time = int(datetime(2024, 9, 1, 1).timestamp() * 1000)  # Earlier time
end_time = int(datetime(2024, 9, 8).timestamp() * 1000)  

granularity = '1m'


