from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from typing import Annotated
import jwt

from ..config import JWT_SECRET_KEY

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def encode_session_token(user_id: str, **kwargs):
    expiration = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,  
        "exp": expiration,
        **kwargs
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_session_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, 
            detail="Session has expired",
            headers={"WWW-Authenticate": "Bearer"}
            )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}  
        )
    
async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    user_id = decode_session_token(token)
    return UUID(user_id)

