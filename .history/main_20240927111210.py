# main.py
# Author: Pau Mateu
# Developer email: paumat17@gmail.com

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.schedule_layer import ScheduleLayer

async_scheduler = ScheduleLayer("Europe/Amsterdam")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    async_scheduler.scheduler.start()
    print("Scheduler started.")
    try:
        yield
    finally:
        # Shutdown the scheduler
        async_scheduler.scheduler.shutdown()
        print("Scheduler shut down.")

app = FastAPI(
    title="Historical Funding Rate API",
    summary="This api recollects every 8 or 4 hours the value of funding rate of bitget in order to get a better analysis",
    lifespan=lifespan
)

origins = [
    "http://0.0.0.0:80",
    "http://localhost:8080",
    "http://3.143.209.3/",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("get_historical_funding_rate/{symbol}/{limit}", description="### Get Historical Funding Rates\n\ From a given symbol returns a list with the historical funding rate and if were a controversial period, provides a analysis about what happened with the price", tags=["Base Funding Rate"])
async def get_gistorical_funding_rate(symbol: str, limit: int):
    return {"response": "under construction"}

@app.get("get_detail_event/{symbol}/{offset}")
async def get_detail_event(symbol: str, offset: int):
    return {"response": "under construction"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)