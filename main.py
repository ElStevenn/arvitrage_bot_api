# main.py
# Author: Pau Mateu
# Developer email: paumat17@gmail.com

from fastapi import FastAPI, HTTPException, Request, WebSocket, Query, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import asyncio

from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.schedule_layer import ScheduleLayer
from app.chart_analysis import FundingRateChart
from app.historcal_funding_rate import MainServiceLayer
from app.schemas import *

async_scheduler = ScheduleLayer("Europe/Amsterdam")
redis_memory = RedisService()
main_services = MainServiceLayer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    async_scheduler.scheduler.start()
    print("Scheduler started.")

    # Schedule the daily job at 9:00 AM Spanish time
    async_scheduler.schedule_daily_job(9, 0, main_services.crypto_rebase)

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


@app.get("/get_historical_funding_rate/{symbol}/{limit}", description="### Get Historical Funding Rates\n\n From a given symbol returns a list with the historical funding rate and if were a controversial period, provides a analysis about what happened with the price", tags=["Base Funding Rate"])
async def get_gistorical_funding_rate(symbol: str, limit: int):
    return {"response": "under construction"}

@app.get("/get_today_analysis/{symbol}", description="### Get today analysis from a given crypto\n\n", tags=["Crypto Analysis"])
async def get_today_analysis(symbol: str):
    chart_analysis = FundingRateChart(symbol)
    period = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Get Analysis
    analysis = await chart_analysis.set_analysis(period)

    return analysis


@app.get("/get_detail_event/{symbol}", description="Get name and logo of the crypto", tags=["Crypto Search"])
async def get_detail_event(symbol: str):
    try:
        crypto_logo, name, description = redis_memory.get_crypto_logo(symbol)

        if symbol.lower().endswith('usdt'):
            symbol = symbol[:-4]

        return {"symbol": symbol, "name": name, "image": crypto_logo, "description": description}
    except TypeError:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")



@app.get(
    "/search",
    description="Search all the available cryptos in the API",
    tags=["Crypto Search"],
    response_model=List[Crypto]
)
async def search_crypto(
    query: Optional[str] = Query(None, description="Search query for symbol or name"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip")
):
    """
    Search for cryptocurrencies based on a query. If no query is provided, returns all cryptos sorted by 'id'.
    
    - **query**: The search string to filter cryptos by symbol or name.
    - **limit**: The maximum number of results to return (default: 50, max: 100).
    - **offset**: The number of results to skip for pagination (default: 0).
    """
    try:
        # Fetch the queried data from Redis
        queried_data = redis_memory.get_list_query(query=query, limit=limit, offset=offset)
        
        # Convert to list of Crypto models
        response = [Crypto(**crypto) for crypto in queried_data]
        
        return response
    except Exception as e:
        # Log the error (optional)
        print(f"Error in /search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@app.websocket("/search-crypto-ws")
async def websocket_search_crypto(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive query and limit from the client
            data = await websocket.receive_json()  # Expecting a JSON with 'query' and 'limit'
            query = data.get('query')
            limit = data.get('limit')

            # Get data from Redis (implement limit if needed)
            queried_data = redis_memory.get_list_query(query=query if query else None)

            # Apply the limit if provided and valid
            if limit and isinstance(limit, int):
                queried_data = queried_data[:limit]

            # Send the queried data back to the WebSocket client
            await websocket.send_json(queried_data)

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        await websocket.close()
        print(f"Error: {e}")





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)