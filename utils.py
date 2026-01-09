from zoneinfo import ZoneInfo
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from db_config import secret_key, algorithm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

SECRET_KEY = secret_key  # 🔒 change in production
ALGORITHM = algorithm

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
    


def current_time_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    


def get_current_user(authorization: str = Header(...)):
    try:
         # Check if header starts with Bearer
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=200, detail="Invalid token")

        token = authorization.split(" ")[1]  # ✅ just the token

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(payload)
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    