import asyncio
from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.chart_analysis import FundingRateChart

bitget_service = BitgetService()
redis_service = RedisService()


async def migrate_model(symbol):
    # Get historical funding rate
    historical_funding_rate = await bitget_service.get_historical_funding_rate(symbol)

    # Get Analysis if was a funding rate greater than 0.5
    for fr_day in historical_funding_rate:
        

    







async def main_tesing():
    symbol = await migrate_model("BTCUSDT")

if __name__ == "__main__":
    asyncio.run(main_tesing())