import socket
import redis
import uuid
import json
import time
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



    def add_new_crypto(self, symbol: str, whole_analysis_until_now: List[dict], fr_expiration: Literal['8h', '4h']):
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

        # Prepare the data structure for saving, incorporating the 'symbol' and 'period'
        new_entry = {
            "symbol": symbol,
            "fr_expiration": fr_expiration,
            "data": whole_analysis_until_now
        }
        self._r.hset("all_crypto_analysis", symbol, json.dumps(new_entry))
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
                return analysis_list[-limit:], analysis_list[""]
            else:
                raise ValueError("'data' field is not a list")
        else:
            raise ValueError("Invalid data format in Redis")


    def get_list_cryptos(self) -> list:
        crypto_list = self._r.get("list_crypto")
        
        if crypto_list:
            try:
                crypto_list = json.loads(crypto_list)
            except json.JSONDecodeError:
                crypto_list = []
        else:
            crypto_list = []

        return crypto_list  

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

    def get_4h_cryptos(self):
        """Get crypto list with expiration time of 4h"""
        pass

    def get_8h_cryptos(self):
        """Get crypto list with expiration time of 8h"""
        pass

    def expiration_time(self, symbol):
        pass

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
    # redis_service.add_new_crypto(symbol, whole_analysis_until_now, '4h')
    # print(redis_service.get_list_cryptos())
    # redis_service.delete_everything()
    # redis_service.delete_crypto(symbol)

    """
    new_period =     {
            "id": str(uuid.uuid4()),
            "period": datetime.now(timezone.utc).isoformat(),
            "funding_rate_value": 0.22,  
            "analysis": {}
        }
    
    redis_service.set_analysis_last_funding(symbol, new_period)
    """
    crypto = redis_service.read_crypto_analysis(symbol)

    for b in crypto:print("*****");print(b)
    print(len(crypto))
    