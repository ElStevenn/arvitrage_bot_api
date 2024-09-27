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
            [
                {
                "id": uuid
                "period": datetime
                "funding_raste_value": float
                "analysis": {
                            "description": ["crypto went down by X% in next 8h", "crypto went down by X% by the first minute", ...]
                            "8h_variation": float,
                            "10m_variation": float,
                            "1m_variation": float
                            } | {}
                
                },
                ...
            ]

        """

        if funding_rate_analysis:
            all_cryptos = json.loads(all_cryptos)


        # Save the updated or new analysis
        self._r.hset("all_crypto_analysis", symbol, json.dumps(all_cryptos))

        # Update the list of cryptos
        crypto_list = self._r.get("list_crypto")
        if crypto_list:
            crypto_list = json.loads(crypto_list)
        else:
            crypto_list = []

        # Add the new symbol to the list of cryptos if it doesn't exist
        if symbol not in crypto_list:
            crypto_list.append(symbol)
            self._r.set("list_crypto", json.dumps(crypto_list))




    def delete_everything(self):
        pass

if __name__ == "__main__":
    redis_service = RedisService()
    