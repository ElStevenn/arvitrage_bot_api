import socket
import redis
from typing import List

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
    def update_funding_rate(self, symbol, funding_rate):
        """Add new funding rate and if it has more than 500 registers, delete the last register"""
        pass

    def set_analysis_last_funding(self, symbol, ):
        pass

    def add_new_crypto(self, symbol: str, whole_analysis_until_now: List[dict]):
        """
            [
                {
                "period": datetime
                "value": float
                "analysis": {
                            "description": ["crypto went down by X% in next 8h", "crypto went down by X% by the first minute", ...]
                            "8h_variation": float,
                            "10m_vairation": float
                            ""
                            } | {}
                
                },
                ...
            ]

        """


        # Update list of cryptos only
        all_cryptos = list(self._r.get("list_crypto"))
        all_cryptos.append(symbol)
        self._r.set("list_crypto", all_cryptos)

    def delete_crypto(self, symbol: str):




        # Update list of cryptos only
        all_cryptos = list(self._r.get("list_crypto"))
        all_cryptos.remove(symbol)
        self._r.set("list_crypto", all_cryptos)

if __name__ == "__main__":
    redis_service = RedisService()
    