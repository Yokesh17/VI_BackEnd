from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from .utils import create_access_token, create_refresh_token, decode_token
from datetime import datetime

from db_config import db, get_connection
from pydantic import BaseModel, EmailStr, Field
from queries import  USERS_SELECT_ALL, USERS_INSERT, LOGIN_USER, LOGIN_USER_WITH_EMAIL
from utils import hash_password, verify_password
from .dependencies import get_current_user

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  
    email: EmailStr  # Validates if the email is in a valid format
    password: str = Field(..., min_length=8) 

class Login(BaseModel):
    username: str  # Can be either username or email
    password: str

router = APIRouter(prefix="/auth")

@router.post("/login")
async def login(response: Response, body : str,  conn=Depends(get_connection)):
    # Check credentials
    data = decode_token(body)
    data = Login(**data)

    is_email = "@" in data.username

    # Select query and parameters
    query = LOGIN_USER_WITH_EMAIL if is_email else LOGIN_USER
    params = {"email": data.username} if is_email else {"username": data.username}
    
    result = await db.read(conn, query,params)
    
    if not result or not verify_password(data.password, result[0]["password"]):
        return {"status": "failure", "message": "invalid username or password"}

    data = {"sub": result}

    # Generate tokens
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    # Send refresh token as HTTP-only cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax")

    return {"access_token": access_token}

@router.post("/signUp")
async def create_user(body: str, conn=Depends(get_connection)):
    # Decode JWT body similar to login endpoint
    data = decode_token(body)
    data = User(**data)

    result = await db.insert(
        conn,
        USERS_INSERT,
        {
            "username": data.username,
            "email": data.email,
            "password": hash_password(data.password),
        },
    )
    return {"status": "success", "data": result}


@router.post("/refresh")
def refresh_token(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = decode_token(refresh_token)
    username = payload.get("sub")

    new_access_token = create_access_token({"sub": username})
    return {"access_token": new_access_token}


@router.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you accessed a protected route!"}








@router.get("/users")
async def list_users(conn=Depends(get_connection)):
    # raise ValueError
    # Both queries happen within a single transaction/connection per request
    result = await db.read(conn, USERS_SELECT_ALL)
    return {"status" : "success" , "data" : result }


# @router.post("/signUp")
# async def create_user(data : User, conn=Depends(get_connection)):
#     result = await db.insert(
#         conn,
#         USERS_INSERT,
#         {"username": data.username, "email": data.email, "password": hash_password(data.password)},
#     )
#     return {"status" : "success","data": result }






