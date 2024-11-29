from typing import TypedDict, Optional, Dict
import asyncio

from .database import ConnectionMongo
from .schema import *

class MongoDB_Crypto(ConnectionMongo):
    def __init__(self):
        super().__init__()

        # Database
        self.db_metadata = self.client["crypto_metadata"]
        self.db_historical_funding_rate = self.client["historical_funding_rate"]

        # Metadata Collections
        self.crypto_collection = self.db_metadata["crypto"]
        self.crypto_list_collection = self.db_metadata["crypto_list"]

        # Historical funding rate Collections
        self.count_collection = self.db_historical_funding_rate["count"]


    # - - - - LIST  CRYPTOS - - - - 
    async def get_avariable_symbol(self) -> list:
        """
        Retrieves a list of available cryptos in a symbol.
        """
        pipeline = [
            {"$group": {"_id": "$symbol"}},
            {"$project": {"_id": 0, "symbol": "$_id"}}
        ]

        # Aggregate pipeline gives an async cursor (DO NOT await here)
        cursor = await self.crypto_collection.aggregate(pipeline)

        # Convert the async cursor to a list
        documents = await cursor.to_list(length=None)

        # Extract and return the symbols
        return [doc["symbol"] for doc in documents]


    
    async def add_new_symbol(self, symbol: str, exchange: str):
        """
        Adds a new symbol to the collection.
        """
        await self.crypto_collection.update_one(
            {"symbol": symbol},
            {"$setOnInsert": {"symbol": symbol, "exchange": exchange}},  
            upsert=True
        )

    async def remove_symbol(self, symbol: str):
        """
        Removes a cryptocurrency by its symbol.
        """
        # Attempt to delete the document
        result = await self.crypto_collection.delete_one({"symbol": symbol})

        # Optional: Debugging or logging
        if result.deleted_count > 0:
            print(f"Successfully removed document with symbol: {symbol}")
        else:
            print(f"No document found with symbol: {symbol}")


    async def remove_all_symbols(self):
        """
        Removes all symbols from the collection.
        """
        await self.crypto_collection.delete_many({})

    # - - - - CRYPTO METADATA - - - -  
    async def add_crypto_metadata(self,  symbol: str, document: Dict):
        """
        Adds metadata for a new cryptocurrency. Also updates the list_crypto.
        """

        await self.crypto_collection.update_one(
            {"symbol": symbol},  
            {"$set": document},  
            upsert=True
        )



    async def get_crypto_metadata(self, symbol: str):
        """
        Retrieves metadata for a given cryptocurrency symbol.
        """
        pass

    async def update_crypto_metadata(self, symbol: str, updates: Dict):
        """
        Updates metadata fields for a given cryptocurrency symbol.
        """
        pass

    async def delete_crypto_metadata(self, symbol: str):
        """
        Deletes metadata for a given cryptocurrency symbol.
        """
        pass


    # - - - CRYPTO FUNDING RATE ANALYSIS - - -

    async def add_funding_rate_analysis(self, symbol: str, funding_rate_analysis: FundingRateAnalysis):
        """
        Adds a new funding rate analysis entry for a given cryptocurrency symbol.
        """
        pass

    async def set_last_analysis(self, symbol: str, analysis_data: Dict):
        """
        Sets the last analysis data for a given cryptocurrency symbol.
        """
        pass

    async def get_funding_rate_history(self, symbol: str, limit: Optional[int] = None):
        """
        Retrieves the funding rate history for a given cryptocurrency symbol.
        """
        pass

    async def get_last_fundng_rate(self, symbol: str):
        """
        Retrieves the last funding rate entry for a given cryptocurrency symbol.
        """
        pass

    async def read_crypto_analysis(self, symbol: str, limit: int = 20):
        """
        Retrieves the latest 'limit' number of analysis entries for a given symbol.
        """
        pass

    async def delete_all_analysis_for_symbol(self, symbol: str):
        """
        Deletes all analysis data for a given cryptocurrency symbol.
        """
        pass

    async def delete_all_analysis(self):
        """
        Deletes all analysis data from all cryptocurrency entries.
        """
        pass


    # - - - UTILITY - - - 


async def mongodb_testing():
    mongo_service = MongoDB_Crypto()

    # await mongo_service.add_new_symbol(symbol='BTCUST')

    # symbols = await mongo_service.get_avariable_symbol(); print(symbols)
    avariable = await mongo_service.remove_symbol('BTCUST'); print(avariable)


if __name__ == "__main__":
    asyncio.run(mongodb_testing())