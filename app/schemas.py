from pydantic import BaseModel
from typing import Optional, List, Literal





# RESPONSE SCHEMA   
class Crypto(BaseModel):
    symbol: str
    name: Optional[str]
    image: Optional[str]
    funding_rate_delay: Literal['8h', '4h']

class CryptoSearch(BaseModel):
    id: int
    symbol: str
    name: Optional[str]
    image: Optional[str]