import socket
import redis
import uuid
import json
from typing import List, Literal

funding_rate_analysis = Literal[
    
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

    def set_analysis_last_funding(self, symbol, ):
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
        # Try to get the existing analysis for the symbol
        all_cryptos = self._r.hget("all_crypto_analysis", symbol)
        
        if all_cryptos:
            # Symbol exists, load its current analysis
            all_cryptos = json.loads(all_cryptos)
            
            # If the number of records exceeds 500, remove the oldest one
            if len(all_cryptos) >= 500:
                all_cryptos.pop(0)
            
            # Add the new analysis
            all_cryptos.append(whole_analysis_until_now)
        else:
            # Symbol doesn't exist, create a new list with the new analysis
            all_cryptos = [whole_analysis_until_now]

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
    