from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime




# RESPONSE SCHEMA   
class Crypto(BaseModel):
    symbol: str
    name: Optional[str]
    image: Optional[str]
    funding_rate_delay: Literal['8h', '4h'] | None
    next_execution_time: datetime | None
    available_in: List[str]

class CryptoSearch(BaseModel):
    id: str
    symbol: str
    name: Optional[str]
    image: Optional[str]