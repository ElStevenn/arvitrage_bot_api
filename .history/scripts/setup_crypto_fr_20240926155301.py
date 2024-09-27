import asyncio
from app.bitget_layer import BitgetService
from app.redis_layer import RedisService

bitget_service = BitgetService()
redis_service = RedisService()


async def migrate_model(symbol):
    # Get historical funding rate
    historical_funding_rate = await bitget_service.get_historical_funding_rate()



if __name__ == "__main__":
    pass