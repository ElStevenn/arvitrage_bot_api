import asyncio, uuid
from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.chart_analysis import FundingRateChart

bitget_service = BitgetService()
redis_service = RedisService()


async def migrate_model(symbol):
    # Get historical funding rate
    historical_funding_rate = await bitget_service.get_historical_funding_rate(symbol)
    crypto_analysis = FundingRateChart(symbol)

    final_model_result = []
    # Get Analysis if was a funding rate greater than 0.5
    for fr_day in historical_funding_rate:
        if fr_day[0] <= -0.5:
            analysis = await crypto_analysis.set_analysis(fr_day[2])
            final_model_result.append({
                "id": uuid.uuid4(),
                "period": fr_day[1],
                "funding_rate_value": fr_day[0],
                "analysis": analysis
            })
            
        else:
            final_model_result.append({
                "id": uuid.uuid4(),
                "period": fr_day[1],
                "funding_rate_value": fr_day[0],
                "analysis": {}
            })

    
    return final_model_result







async def main_tesing():
    symbol = await migrate_model("BTCUSDT")
    print(symbol)

if __name__ == "__main__":
    asyncio.run(main_tesing())