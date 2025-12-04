from zoneinfo import ZoneInfo
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "3213d8b8908c6224acad88f034b3a39eb46cdd3d40ae817a26beb930a1870353"  # 🔒 change in production
ALGORITHM = "HS256wevgw"

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def current_time_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata"))


