import socket
import redis
import uuid
import json
from typing import List, Literal, Dict
from datetime import datetime


funding_rate_analysis = Literal[
    Dict[
        "id": uuid,
        "period": datetime,
        "funding_rate_value": float,
        "analysis": {

        }
    ]
]


class RedisService:
    def __init__(self) -> None:
        hostname = socket.gethostname()

        if hostname == 'mamadocomputer':
            redis_host = ''
            port = ''
        else: 
            redis_host = ''
            port = ''
        
        self._r = redis.Redis(host='localhost', port='6378', decode_responses=True)

    # FUNDING RATE
    def update_funding_rate(self, symbol, funding_rate, ):
        """Add new funding rate and if it has more than 500 registers, delete the last register"""
        pass

    def set_analysis_last_funding(self, symbol, funding_rate_analysis: funding_rate_analysis | None = None):
        pass

    def add_new_crypto(self, symbol: str, whole_analysis_until_now: List[dict]):
        """
        Adds a new cryptocurrency analysis to the Redis database. If the crypto does not exist, 
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
        all_cryptos = self._r.hget("all_crypto_analysis", symbol)

        if not all_cryptos:
            all_cryptos = [whole_analysis_until_now]
        else:
            all_cryptos = json.loads(all_cryptos)
            if len(all_cryptos) >= 500:
                all_cryptos.pop(0)
            
            # Add the new analysis
            all_cryptos.append(whole_analysis_until_now)

        # Save the updated or new analysis for this symbol
        self._r.hset("all_crypto_analysis", symbol, json.dumps(all_cryptos))

        # Update the list of cryptos only if the symbol doesn't already exist
        crypto_list = self._r.get("list_crypto")
        if crypto_list:
            crypto_list = json.loads(crypto_list)
        else:
            crypto_list = []

        if symbol not in crypto_list:
            crypto_list.append(symbol)
            self._r.set("list_crypto", json.dumps(crypto_list))




    def delete_everything(self):
        pass

if __name__ == "__main__":
    redis_service = RedisService()
    