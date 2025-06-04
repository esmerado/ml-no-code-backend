from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .jwt_handler import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# TODO: Check this use

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload  # puedes devolver un dict con email, id, etc.
