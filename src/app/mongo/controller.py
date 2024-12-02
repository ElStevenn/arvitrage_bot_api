from typing import TypedDict, Optional, Dict
from bson import ObjectId
import asyncio, re

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
        cursor = await self.crypto_list_collection.aggregate(pipeline)

        # Convert the async cursor to a list
        documents = await cursor.to_list(length=None)

        # Extract and return the symbols
        return [doc["symbol"] for doc in documents]



    async def add_new_symbol(self, symbol: str, exchange: str):
        """
        Adds a new symbol to the collection.
        """
        await self.crypto_list_collection.update_one(
            {"symbol": symbol},
            {
                "$setOnInsert": {"symbol": symbol},  # Initialize 'symbol' if the document is inserted
                "$addToSet": {"exchange": exchange}  # Add 'exchange' to the array if not already present
            },
            upsert=True
        )


    async def remove_symbol(self, symbol: str):
        """
        Removes a cryptocurrency by its symbol.
        """
        # Attempt to delete the document
        result = await self.crypto_list_collection.delete_one({"symbol": symbol})

        # Optional: Debugging or logging
        if result.deleted_count > 0:
            print(f"Successfully removed document with symbol: {symbol}")
        else:
            print(f"No document found with symbol: {symbol}")


    async def remove_all_symbols(self):
        """
        Removes all symbols from the collection.
        """
        await self.crypto_list_collection.delete_many({})

    # - - - - CRYPTO METADATA - - - -  
    async def add_crypto_metadata(self, symbol: str, document: Dict):
        """
        Adds metadata for a cryptocurrency or updates it if the symbol already exists.
        """

        result = await self.crypto_collection.update_one(
            {"symbol": symbol},  # Match by symbol
            {"$set": document},  # Update the fields in the document
            upsert=True          # Insert if no document matches
        )
        
        print(f"Matched Count: {result.matched_count}, Modified Count: {result.modified_count}, Upserted ID: {result.upserted_id}")

    async def search_metadata(self, query: str, limit: int = 20, offset: int = 0):
        # First, search for exact matches
        exact_filter = {
            "$or": [
                {"symbol": query.upper()},
                {"name": query}
            ]
        }
        
        # Then, search for partial matches using regex
        # Escape special regex characters in the query
        escaped_query = re.escape(query)
        pattern = re.compile(escaped_query, re.IGNORECASE)
        regex_filter = {
            "$or": [
                {"symbol": pattern},
                {"name": pattern}
            ]
        }
        
        # Exclude documents already found in exact matches
        exclude_ids = set()
        exact_cursor = self.crypto_collection.find(exact_filter)
        exact_results = []
        async for document in exact_cursor:
            document['id'] = str(document['_id'])
            del document['_id']
            document['match_type'] = 'exact'
            exact_results.append(document)
            exclude_ids.add(document['id'])
        
        # Modify regex filter to exclude exact matches
        if exclude_ids:
            regex_filter['_id'] = {"$nin": [ObjectId(id) for id in exclude_ids]}
        
        # Apply limit and offset after combining results
        remaining_limit = limit - len(exact_results)
        if remaining_limit > 0:
            regex_cursor = self.crypto_collection.find(regex_filter).skip(offset).limit(remaining_limit)
            regex_results = []
            async for document in regex_cursor:
                document['id'] = str(document['_id'])
                del document['_id']
                document['match_type'] = 'partial'
                regex_results.append(document)
        else:
            regex_results = []
        
        # Combine results, exact matches first
        results = exact_results + regex_results
        
        return results


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


    data = {
        "symbol": "1INCH",
        "name": "Mamado Network",
        "description": "1inch Network (1INCH) is a cryptocurrency launched in 2020and operates on the Ethereum platform. 1inch Network has a current supply of 1,500,000,000 with 1,321,595,936.46216 in circulation. The last known price of 1inch Network is 0.43737438 USD and is up 0.53 over the last 24 hours. It is currently trading on 507 active market(s) with $110,597,662.60 traded over the last 24 hours. More information can be found at https://1inch.io/.",
        "logo": "https://s2.coinmarketcap.com/static/img/coins/128x128/8104.png",
        "urls": {
            "website": [
            "https://1inch.io/"
            ],
            "twitter": [
            "https://twitter.com/1inch"
            ],
            "message_board": [
            "https://blog.1inch.io/"
            ],
            "chat": [
            "https://t.me/OneInchNetwork",
            "https://discord.com/invite/1inch"
            ],
            "facebook": [
            "https://www.facebook.com/1inchNetwork"
            ],
            "explorer": [
            "https://solscan.io/token/AjkPkq3nsyDe1yKcbyZT7N4aK4Evv9om9tzhQD3wsRC",
            "https://etherscan.io/token/0x111111111117dc0aa78b770fa6a738034120c302",
            "https://nearblocks.io/token/111111111117dc0aa78b770fa6a738034120c302.factory.bridge.near",
            "https://blockscout.com/xdai/mainnet/tokens/0x7f7440C5098462f833E123B44B8A03E1d9785BAb/token-transfers",
            "https://bscscan.com/token/0x111111111117dc0aa78b770fa6a738034120c302"
            ],
            "reddit": [
            "https://reddit.com/r/1inch"
            ],
            "technical_doc": [
            "https://docs.1inch.io/"
            ],
            "source_code": [
            "https://github.com/1inch"
            ],
            "announcement": []
        },
        "date_added": "2024-12-02T11:56:17.819878",
        "tags": [
            "decentralized-exchange-dex-token",
            "defi",
            "wallet",
            "amm",
            "binance-labs-portfolio",
            "blockchain-capital-portfolio",
            "dragonfly-capital-portfolio",
            "fabric-ventures-portfolio",
            "alameda-research-portfolio",
            "parafi-capital",
            "spartan-group",
            "bnb-chain",
            "celsius-bankruptcy-estate"
        ],
        "decimals": None,
        "max_supply": None,
        "funding_rate_interval": "8",
        "available_in": [
            "bitget",
            "binance"
        ],
        "blockchain": None,
        "token_type": None,
        "genesis_date": None,
        "consensus_mechanism": None,
        "price_spread": None,
        "historical_ohlc_url": None,
        "funding_rate_history_url": None,
        "average_gas_cost": None,
        "average_volatility": None,
        "network_activity": None,
        "use_cases": []
        }

    # symbols = await mongo_service.get_avariable_symbol(); print(symbols)
    avariable = await mongo_service.search_metadata("1in"); print(avariable)


if __name__ == "__main__":
    asyncio.run(mongodb_testing())