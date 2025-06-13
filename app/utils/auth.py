# utils/auth.py
import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.utils.supabase_utils import get_user_data

load_dotenv()
SECRET_KEY = os.getenv("NEXTAUTH_SECRET")
ALGORITHM = "HS256"

auth_scheme = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials

    try:

        payload = jwt.get_unverified_claims(token)

        verified_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = verified_payload.get("id")

        user = get_user_data(user_id=user_id)

        user_type = user.get("user_type")

        verified_payload["user_type"] = user_type

        return verified_payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
