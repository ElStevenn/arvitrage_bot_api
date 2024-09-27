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
        self._r.hset("list_crypto")

    def delete_crypto(self, symbol: str):
        self._r.delete("list_crypto")

if __name__ == "__main__":
    redis_service = RedisService()
    