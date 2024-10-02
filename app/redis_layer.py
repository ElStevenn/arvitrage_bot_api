import socket
import redis
import uuid
import json
import time
import re
import numpy as np
from typing import List, Literal, Dict, TypedDict, Optional, Tuple
from datetime import datetime, timezone
from pprint import pprint

class FundingRateAnalysis(TypedDict, total=False):
    id: uuid.UUID
    period: datetime
    funding_rate_value: float
    analysis: Optional[dict]

class Analysis(TypedDict, total=False):
    description: List[str]
    eight_hour_variation: float
    ten_minute_variation: float
    one_minute_variation: float

class RedisService:
    def __init__(self) -> None:
        hostname = socket.gethostname()

        if hostname == 'mamadocomputer':
            redis_host = 'localhost'
            port = '6378'
        else: 
            redis_host = ''
            port = ''
        
        self._r = redis.Redis(host=redis_host, port=port, decode_responses=True)

    # FUNDING RATE
    def set_analysis_last_funding(self, symbol: str, funding_rate_analysis: FundingRateAnalysis):
        """
        Adds a new analysis or just a new funding rate attached to the symbol.
        {
            "id": uuid,
            "period": datetime,
            "funding_rate_value": float,
            "analysis": {
                "description": ["crypto went down by X% in next 8h", "crypto went down by X% by the first minute", ...],
                "8h_variation": float,
                "10m_variation": float,
                "1m_variation": float
            } | {}
        }
        """
        # Fetch existing data for the symbol
        existing_data = self._r.hget("all_crypto_analysis", symbol)

        if not existing_data:
            new_data = {
                "symbol": symbol,
                "data": [funding_rate_analysis]
            }
        else:
            existing_data = json.loads(existing_data)
            
            # Ensure "data" field exists and is a list
            if "data" in existing_data and isinstance(existing_data["data"], list):
                if len(existing_data["data"]) >= 500:
                    existing_data["data"].pop(0) 
                existing_data["data"].append(funding_rate_analysis)
            else:
                existing_data["data"] = [funding_rate_analysis]
            new_data = existing_data

        self._r.hset("all_crypto_analysis", symbol, json.dumps(new_data))



    def add_new_crypto(self, symbol: str, picture_url, whole_analysis_until_now: List[dict], fr_expiration: Literal['8h', '4h']):
        """
        Creates a new cryptocurrency analysis to the Redis database. If the crypto does not exist, 
        it will create the entry and ensure the number of records is limited to 500.

        whole_analysis_until_now: [
            "symbol": str
            "fr_expiration": str,
            "data": {
                    "id": uuid,
                    "period": datetime,
                    "funding_raste_value": float,
                    "analysis": {
                        "description": ["crypto went down by X% in next 8h", "crypto went down by X% by the first minute", ...],
                        "8h_variation": float,
                        "10m_variation": float,
                        "1m_variation": float
                        ...
                    } | {}
                }
        ]
        """

        crypto_data = self._r.hget("all_crypto_analysis", symbol)
        if crypto_data:
            return  

        # Prepare the data structure for saving
        new_entry = {
            "symbol": symbol,
            "picture_url": picture_url,
            "fr_expiration": fr_expiration,
            "data": whole_analysis_until_now
        }
        self._r.hset("all_crypto_analysis", symbol, json.dumps(new_entry))

        # Update list_crypto
        crypto_list = self._r.get("list_crypto")
        if crypto_list:
            try:
                crypto_list = json.loads(crypto_list)
            except json.JSONDecodeError:
                crypto_list = []
        else:
            crypto_list = []

        # Add the symbol if it’s not already in the list
        if symbol not in crypto_list:
            crypto_list.append(symbol)
            self._r.set("list_crypto", json.dumps(crypto_list))

    def add_symbol_only(self, symbol: str, name, picture_url: str, description: str):
            """
            Adds a new symbol with its picture to the Redis database.
            """
            # Check if the symbol already exists
            existing_data = self._r.hget("all_crypto_analysis", symbol)
            id = self.add_crypto_offset()
            if existing_data:
                return  # Symbol already exists

            # Create a new entry with symbol and picture
            new_entry = {
                "id": int(id),
                "symbol": symbol,
                "name": name,
                "picture_url": picture_url,
                "description": description,
                "data": [],
            }
            self._r.hset("all_crypto_analysis", symbol, json.dumps(new_entry))

            # Add the symbol to the list_crypto
            crypto_list = self._r.get("list_crypto")
            if crypto_list:
                try:
                    crypto_list = json.loads(crypto_list)
                except json.JSONDecodeError:
                    crypto_list = []
            else:
                crypto_list = []

            if symbol not in crypto_list:
                crypto_list.append(symbol)
                self._r.set("list_crypto", json.dumps(crypto_list))




    def read_crypto_analysis(self, symbol: str, limit: int = 20) -> Tuple[list, str]:
        # Fetch the data for the specified symbol from Redis
        crypto_data = self._r.hget("all_crypto_analysis", symbol)
        
        # If no data exists for the symbol, return an empty list
        if not crypto_data:
            return []
        
        # Load the JSON data from Redis
        crypto_data = json.loads(crypto_data)
        
        # Ensure that the 'data' field exists and is a list
        if isinstance(crypto_data, dict) and "data" in crypto_data:
            analysis_list = crypto_data["data"]
            
            if isinstance(analysis_list, list):
                # Return the latest 'limit' number of records
                return analysis_list[-limit:], crypto_data["fr_expiration"]
            else:
                raise ValueError("'data' field is not a list")
        else:
            raise ValueError("Invalid data format in Redis")


    def get_list_cryptos(self):
        crypto_list = self._r.get("list_crypto")
        
        if crypto_list:
            try:
                crypto_list = json.loads(crypto_list)
            except json.JSONDecodeError:
                crypto_list = []
        else:
            crypto_list = []

        return np.array(crypto_list)  

    def get_all_cryptos(self):
        """
        Get all cryptos detailed
        """
        all_symbols = self.get_list_cryptos()

        result = []
        for symbol in all_symbols:
            crypto_data = self.get_crypto_essential(symbol)
            result.append(crypto_data)
        
        return result

    def get_list_query(self, query: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = 0) -> List[Dict]:
        """
        Retrieves a list of cryptocurrencies based on the provided query with pagination.
        
        - If no query is provided, returns all cryptos sorted by 'id' in ascending order.
        - If a query is provided, searches both 'symbol' and 'name' (case-insensitive).
          Results are ordered first by those that start with the query, then those that contain it.
        
        Args:
            query (Optional[str]): The search query string.
            limit (Optional[int]): Number of results to return.
            offset (Optional[int]): Number of results to skip.
        
        Returns:
            List[Dict]: A list of dictionaries containing cryptocurrency data.
        """
        
        # Fetch all cryptocurrencies
        all_cryptos = self.get_all_cryptos()
        
        if not query:
            # No query provided; sort all cryptos by 'id' ascending
            sorted_all = sorted(
                all_cryptos, 
                key=lambda x: x.get('id', float('inf')) if isinstance(x.get('id', None), int) else float('inf')
            )
        else:
            # Normalize the query for case-insensitive comparison
            query_lower = query.lower()
            
            starts_with = []
            contains = []
            
            for crypto in all_cryptos:
                symbol = crypto.get('symbol', '').lower()
                name = crypto.get('name', '').lower()
                
                # Check if 'symbol' or 'name' starts with the query
                if symbol.startswith(query_lower) or name.startswith(query_lower):
                    starts_with.append(crypto)
                # Check if 'symbol' or 'name' contains the query
                elif query_lower in symbol or query_lower in name:
                    contains.append(crypto)
            
            # Sort each list by 'id' ascending to maintain consistency
            starts_with_sorted = sorted(
                starts_with, 
                key=lambda x: x.get('id', float('inf')) if isinstance(x.get('id', None), int) else float('inf')
            )
            contains_sorted = sorted(
                contains, 
                key=lambda x: x.get('id', float('inf')) if isinstance(x.get('id', None), int) else float('inf')
            )
            
            # Combine the lists: starts_with first, then contains
            sorted_all = starts_with_sorted + contains_sorted
        
        # Apply offset and limit
        if offset:
            sorted_all = sorted_all[offset:]
        if limit:
            sorted_all = sorted_all[:limit]
        
        return sorted_all





    def delete_everything(self):
        self._r.flushall()

    def delete_crypto(self, symbol):
        self._r.hdel("all_crypto_analysis", symbol)

        crypto_list = self._r.get("list_crypto")

        if crypto_list:
            try:
                crypto_list = json.loads(crypto_list)
            except json.JSONDecodeError:
                crypto_list = []

        if symbol in crypto_list:
            crypto_list.remove(symbol)

            self._r.set("list_crypto", json.dumps(crypto_list))

    def get_crypto_logo(self, symbol: str) -> Tuple[str, str, str]:
        """
        Retrieves the picture URL (logo) for the given cryptocurrency symbol.
        """
        crypto_data = self._r.hget("all_crypto_analysis", symbol)
        if not crypto_data:
            return None
        crypto_data = json.loads(crypto_data)
        return crypto_data.get("picture_url", None), crypto_data.get("name", None), crypto_data.get("description", None)

    def get_crypto_essential(self, symbol) -> dict:
        """
        Retrives the essential data from a given crypto (name and id)
        """
        crypto_data = self._r.hget("all_crypto_analysis", symbol)
        if not crypto_data:
            return None
        crypto_data = json.loads(crypto_data)

        return {"id": crypto_data.get('id', None), "symbol": str(symbol), "name": crypto_data.get('name', None), "image": crypto_data.get('picture_url', None)}

    def get_4h_cryptos(self) -> List[str]:
        """Get a list of cryptos with a funding rate expiration time of 4h."""
        crypto_list = self.get_list_cryptos()
        cryptos_with_4h = []
        
        for symbol in crypto_list:
            expiration_time = self.expiration_time(symbol)
            if expiration_time == "4h":
                cryptos_with_4h.append(symbol)
        
        return cryptos_with_4h

    def get_8h_cryptos(self) -> List[str]:
        """Get a list of cryptos with a funding rate expiration time of 8h."""
        
        crypto_list = self.get_list_cryptos()
        cryptos_with_8h = []
        
        for symbol in crypto_list:
            expiration_time = self.expiration_time(symbol)
            if expiration_time == "8h":
                cryptos_with_8h.append(symbol)
        
        return cryptos_with_8h

    def expiration_time(self, symbol):
        crypto_data = json.loads(self._r.hget("all_crypto_analysis", symbol))

        if not crypto_data:
            return None

        return crypto_data["fr_expiration"]

    def add_crypto_offset(self):
        """Add 1 to crypto offset"""
        count = json.loads(self._r.get("crypto_count") or "0")                   
        if not count:
            count = 1
        else:
            count += 1
        
        self._r.set("crypto_count", count)

        return count
        

## TESTING & EXAMPLE OF REDIS ## 
if __name__ == "__main__":
    redis_service = RedisService()

    # Test data
    symbol = "DOGUSDT"
    whole_analysis_until_now = [
        {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat()
            ,
            "funding_rate_value": 0.55,  # Funding rate > 0.5, includes analysis
            "analysis": {
                "description": [
                    "crypto went up by 5% in the next 8 hours",
                    "crypto dropped by 2% in the first 10 minutes",
                    "steady increase of 0.1% every minute after initial drop"
                ],
                "8h_variation": 5.0,
                "10m_variation": -2.0,
                "1m_variation": 0.1,
                "daily_trend": "bullish",
                "weekly_trend": "slightly bullish",
                "volatility_index": 1.5,
                "average_trading_volume": 1000000,
                "market_sentiment": "positive"
            }
        },
        {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.45,
            "analysis": {}
        },
        {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.6,  
            "analysis": {
                "description": [
                    "massive spike of 10% in 30 minutes due to external market factors",
                    "sharp correction of 3% within the next 4 hours",
                    "volatile movements due to speculation"
                ],
                "8h_variation": 7.0,
                "10m_variation": 2.5,
                "1m_variation": 1.0,
                "daily_trend": "highly volatile",
                "weekly_trend": "bullish",
                "volatility_index": 3.0,
                "average_trading_volume": 5000000,
                "market_sentiment": "highly speculative"
            }
        },
        {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.3,  
            "analysis": {}
        },
        {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.75,  
            "analysis": {
                "description": [
                    "steady increase of 0.5% per hour over 8 hours",
                    "positive sentiment due to upcoming major news announcement"
                ],
                "8h_variation": 4.0,
                "10m_variation": 0.5,
                "1m_variation": 0.05,
                "daily_trend": "bullish",
                "weekly_trend": "slightly bullish",
                "volatility_index": 1.0,
                "average_trading_volume": 2000000,
                "market_sentiment": "anticipatory positive"
            }
        }
    ]


    # Call the add_new_crypto method
    # redis_service.add_new_crypto(symbol, None, whole_analysis_until_now, '4h')
    # print(redis_service.get_list_cryptos())
    # redis_service.delete_everything()
    print(redis_service.get_list_query("bit"))
    # print(redis_service.get_crypto_logo("BTCUSDT"))

    """
    new_period =     {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.22,  
            "analysis": {}
        }
    
    redis_service.set_analysis_last_funding(symbol, new_period)
    """
    # crypto = redis_service.read_crypto_analysis(symbol)

    # print(redis_service.get_4h_cryptos())
    


    