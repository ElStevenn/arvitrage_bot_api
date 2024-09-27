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
        self.ensure_correct_key_type()

    def ensure_correct_key_type(self):
        """Ensure the 'tasks' key is a hash or delete it if not."""
        if self._r.exists("tasks") and self._r.type("tasks") != "hash":
            print(f"Deleting the incorrect 'tasks' key of type {self._r.type('tasks')}.")
            self._r.delete("tasks")

    def update_funding_rate(self, symbol, funding_rate):
        """Add new funding rate and if it has more than 500 registers, delete the last"""
        pass

    def set_analysis_last_funding(self, symbol, ):
        pass

    def add_new_crypto(self, symbol: str, whole_analysis_until_now: List[dict]):
        pass


if __name__ == "__main__":
    quit()