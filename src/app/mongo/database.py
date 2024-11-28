from pymongo import AsyncMongoClient
from urllib.parse import quote_plus
import socket

from src.config import MONGO_USER, MONGO_PASSWD
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
                f"mongodb://{MONGO_USER}:{password_encoded}@mongo_container:27017/?authSource=admin"
            )

        # Database
        self.db_metadata = self.client["crypto_metadata"]
        self.db_historical_funding_rate = self.client["historical_funding_rate"]

        # Metadata Collections
        self.crypto_collection = self.db_metadata["crypto"]
        self.crypto_list_collection = self.db_metadata["crypto_list"]

        # Historical funding rate Collections
        self.count_collection = self.db_historical_funding_rate["count"]

    async def get_databases(self):
        databases = await self.client.list_database_names()
        return databases

async def mongodb_main_testing():
    mongo = ConnectionMongo()

    res = await mongo.get_databases()
    print(res)
    

if __name__ == "__main__":
    asyncio.run(mongodb_main_testing())