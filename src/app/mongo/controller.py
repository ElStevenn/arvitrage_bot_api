from .database import ConnectionMongo


class MongoDB_Crypto(ConnectionMongo):
    def __init__(self):
        super().__init__()