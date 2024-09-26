# main.py
# Author: Pau Mateu
# Developer email: paumat17@gmail.com

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.bitget_layer import BitgetService
from app.redis_layer import RedisService
from app.schedule_layer import ScheduleService

app = FastAPI(
    title="Historical "
)








if __name__ == "__main__":
    pass