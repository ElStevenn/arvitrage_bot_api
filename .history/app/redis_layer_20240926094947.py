import socket


class RedisService:
    def __init__(self) -> None:
        host = socket.gethostname()

        if 