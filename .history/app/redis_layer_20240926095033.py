import socket
import redis

class RedisService:
    def __init__(self) -> None:
        hostname = socket.gethostname()

        if hostname == 'mamadocomputer':
            redis_host = ''
            port = ''
        else: 
            redis_host = ''
            port = ''