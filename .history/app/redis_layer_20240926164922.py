import socket
import redis
import uuid
import json
from typing import List, Literal, Dict, TypedDict, Optional
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
                "funding_raste_value": float,
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

        # If no data exists, create a new list with the provided funding rate analysis
        if not existing_data:
            new_data = [funding_rate_analysis]
        else:
            # Load existing data and append the new analysis
            new_data = json.loads(existing_data)
            
            # Optionally, enforce a limit on the number of records (if needed)
            if len(new_data) >= 500:
                new_data.pop(0)
            
            new_data.append(funding_rate_analysis)

        # Save the updated analysis data back to Redis
        self._r.hset("all_crypto_analysis", symbol, json.dumps(new_data))


    def add_new_crypto(self, symbol: str, whole_analysis_until_now: List[dict], period: Literal['8h', '4h']):
        """
        Creates a new cryptocurrency analysis to the Redis database. If the crypto does not exist, 
        it will create the entry and ensure the number of records is limited to 500.

        whole_analysis_until_now: [
            {
                "id": uuid,
                "period": datetime,
                "funding_raste_value": float,
                "analysis": {
                    "description": ["crypto went down by X% in next 8h", "crypto went down by X% by the first minute", ...],
                    "8h_variation": float,
                    "10m_variation": float,
                    "1m_variation": float
                } | {}
            }
        ]
        """
        crypto_data = self._r.hget("all_crypto_analysis", symbol)

        # Save new crypto
        if not crypto_data:
            crypto_data = [whole_analysis_until_now]
        else:
            crypto_data = json.loads(crypto_data)
            if len(crypto_data) >= 500:
                crypto_data.pop(0)
            crypto_data.append(whole_analysis_until_now)

        self._r.hset("all_crypto_analysis", symbol, json.dumps(crypto_data))


        # Update the list of cryptos only if the symbol doesn't already exist
        crypto_list = self._r.get("list_crypto")
        if crypto_list:
            crypto_list = json.loads(crypto_list)
        else:
            crypto_list = []

        if symbol not in crypto_list:
            crypto_list.append(symbol)
            self._r.set("list_crypto", json.dumps(crypto_list))

    def read_crypto_analysis(self, symbol, limit: int = 20):
        crypto_data = self._r.hget("all_crypto_analysis", symbol)
        if not crypto_data:
            return []
        
        crypto_data = json.loads(crypto_data)
        return crypto_data[-limit:]


    def delete_everything(self):
        self._r.flushall()

    



## TESTING & EXAMPLE OF REDIS ## 
if __name__ == "__main__":
    redis_service = RedisService()

    # Test data
    symbol = "BTC"
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
    # redis_service.add_new_crypto(symbol, whole_analysis_until_now)
    crypto = redis_service.read_crypto_analysis(symbol)
    pprint(crypto)