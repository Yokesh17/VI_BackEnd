from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from .utils import create_access_token, create_refresh_token, decode_token
from datetime import datetime
from db_config import  get_db_connection as get_connection, get_data, get_datas, execute_query, update, return_update, insert, return_insert, execute_returning_one, execute_all
from pydantic import BaseModel, EmailStr, Field
from queries import  USERS_SELECT_ALL, USERS_INSERT, LOGIN_USER, LOGIN_USER_WITH_EMAIL
from utils import hash_password, verify_password
from .dependencies import get_current_user
import base64
import json
from datetime import datetime, date
from .auth_checks import validate_user

class User(BaseModel):
    username: str 
    email: str  # Validates if the email is in a valid format
    password: str

class Login(BaseModel):
    username: str  # Can be either username or email
    password: str

class LoginPayload(BaseModel):
    body: str

router = APIRouter(prefix="/auth")


@router.post("/login")
def login(response: Response, payload: LoginPayload,  conn=Depends(get_connection)):
    # Check credentials
    data = json.loads(base64.b64decode(payload.body).decode("utf-8"))
    data = Login(**data)

    is_email = "@" in data.username

    # Select query and parameters
    query = LOGIN_USER_WITH_EMAIL if is_email else LOGIN_USER
    params = {"email": data.username} if is_email else {"username": data.username}
    
    result = execute_query(conn, query,params)
    
    if not result or not verify_password(data.password, result[0]["password"]):
        return {"status": "failure", "message": "invalid username or password"}

    data = {"sub": result}

    # Generate tokens
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    # Send refresh token as HTTP-only cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax")

    return {"status" : "success","access_token": access_token}

@router.post("/signUp")
def create_user(payload: LoginPayload):
    # Decode body similar to login endpoint
    decoded = base64.b64decode(payload.body).decode("utf-8")
    user_data = json.loads(decoded)
    data = User(**user_data)

    if validate_user(data).get("status")=="failure":
        return validate_user(data)

    # Execute insert in a single, short-lived connection suitable for transaction pooling
    # result = execute_returning_one(
    #     USERS_INSERT,
    #     {
    #         "username": data.username,
    #         "email": data.email,
    #         "password": hash_password(data.password),
    #     },
    # ), "data": result["id"]
    return {"status": "success"}


@router.post("/refresh")
def refresh_token(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = decode_token(refresh_token)
    username = payload.get("sub")

    new_access_token = create_access_token({"sub": username})
    return {"status" : "success" ,"access_token": new_access_token}


@router.post("/check-details")
def check_details(payload : dict):
    if payload.get("dob"):
        dob = datetime.strptime(payload.get("dob"), "%Y-%m-%d").date()
        today = date.today()

        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
    else: 
        return {"status": "failure", "message": "Date of birth is required"}

    return {"status": "success", "data": {"age" : age , "gender" : payload.get("gender")}}


@router.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you accessed a protected route!"}








# @router.get("/users")
# def list_users():
#     result = execute_all(USERS_SELECT_ALL)
# pen within a single transaction/connection per request
#     result = await db.read(conn, USERS_SELECT_ALL)






