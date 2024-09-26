# main.py
# Author: Pau Mateu
# Developer email: paumat17@gmail.com

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.schedule_layer import ScheduleService



app = FastAPI(
    title="Historical Funding Rate API",
    summary="This api recollects every 8 or 4 hours the value of funding rate of bitget in order to get a better analysis"
)


@app.get("get_historical_funding_rate/{symbol}/{limit}", description="### Get Historical Funding Rates\n\nBasically grom a given symbol returns a list with the historical funding rate and if were a controversial period, provides a analysis about what happened with the price", tags=["Base Funding Rate"])
async def get_gistorical_funding_rate(symbol: str, limit: int):
    return {}



if __name__ == "__main__":
    import uvicorn
    pass