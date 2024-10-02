from pydantic import BaseModel
from typing import Optional, List





# RESPONSE SCHEMA   
class Crypto(BaseModel):
    id: Optional[int]
    symbol: str
    name: Optional[str]
    image: Optional[str]
