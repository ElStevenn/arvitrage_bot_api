from pymongo import AsyncMongoClient
from urllib.parse import quote_plus
import socket

from src.config import MONGO_USER, MONGO_PASSWD, MONGODB_URL
import asyncio

hostname = socket.gethostname()
password_encoded = quote_plus(MONGO_PASSWD)

"""
https://chatgpt.com/c/6729dbc3-18bc-800e-acc4-47e62229d3cb

"""

class ConnectionMongo:
    def __init__(self):
        if hostname == 'mamadocomputer' or hostname == 'pauserver':
            self.client = AsyncMongoClient(
                f"mongodb://{MONGO_USER}:{password_encoded}@localhost:27017/?authSource=admin"
            )
        else:
            self.client = AsyncMongoClient(
                f"mongodb://{MONGO_USER}:{password_encoded}@mongodb_v1:27017/?authSource=admin"
            )

    async def get_databases(self):
        databases = await self.client.list_database_names()
        return databases

async def mongodb_main_testing():
    mongo = ConnectionMongo()

    res = await mongo.get_databases()
    print(res)
    

if __name__ == "__main__":
    asyncio.run(mongodb_main_testing())