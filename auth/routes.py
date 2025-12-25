from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from .utils import create_access_token, create_refresh_token, decode_token
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, BaseModel
from typing import Union, Literal
import base64
import json
from datetime import datetime, date

from utils import hash_password, verify_password
from .dependencies import get_current_user
from .auth_checks import validate_user, details_check
from db_config import  get_db_connection as get_connection, get_data, get_datas, execute_query, update, return_update, insert, return_insert, execute_returning_one, execute_all

from queries.create_tables import   LOGIN_USER, LOGIN_USER_WITH_EMAIL
from queries.fetch_data import USERS_SELECT_ALL, USER_INFO
from queries.updates import USERS_INSERT,USERS_DETAILS_INSERT,USERS_UPDATE_EMAIL_VERIFY, USERS_UPDATE_PHONE_VERIFY, USER_DETAILS_UPDATE_PHONE

def parse_date(date_str: str):
    if date_str: return datetime.strptime(date_str, "%d-%m-%Y").date()

class User(BaseModel):
    username: str 
    email: str  # Validates if the email is in a valid format
    password: str


class userPayload(BaseModel):
    userName: str 
    name: str 
    gender: str 
    date_of_birth: str 
    email: str 
    password : str 
    otp: str 
    type : Literal["email"]

class mobileOTP(BaseModel):
    type: Literal["mobile"]
    phone: str
    otp: str

UserDetails = Union[userPayload, mobileOTP]

    

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
    # try:
    #     result = execute_returning_one(
    #         USERS_INSERT,
    #         {
    #             "username": data.username,
    #             "email": data.email,
    #             "password": hash_password(data.password),
    #         },
    #     ) 
    # except Exception as e:  
    #     if "users_username_key" in str(e):
    #         message = "Username already exists"
    #     elif "users_email_key" in str(e):
    #         message = "Email already exists"
    #     return {"status": "failure", "message": message}

    return {"status": "success" }


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
    return details_check(payload)

@router.post("/otp-verify")
def verify_otp(response: Response, data: UserDetails):
    # data = UserDetails(**payload)

    if len(data.otp) != 4:  return {"status": "failure", "message": "Invalid OTP"}

    if data.type == 'email':
        result = execute_returning_one(
            USERS_INSERT,
            {
                "username": data.userName,
                "email": data.email,
                "password": hash_password(data.password),
                "email_verified": True
            },
        ) 

        results = execute_returning_one(
            USERS_DETAILS_INSERT,
            {
                "user_id": result["id"],
                "mobile_number": data.phone,    
                "full_name": data.name,
                "gender": data.gender,
                "date_of_birth": parse_date(data.date_of_birth),
                # "age": payload.get('age'),
            },
        )

        # Generate tokens
        access_token = create_access_token(results)
        refresh_token = create_refresh_token(results)
        # Send refresh token as HTTP-only cookie
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax")
        return {"status" : "success", "message": "OTP verified successfully","access_token": access_token}

    elif data.type == 'mobile':
        update_mobile = execute_returning_one(
            USERS_UPDATE_PHONE_VERIFY,
            {
               "user_id": 20
            },
        ) 
        update_mobile_otp = execute_returning_one(
            USER_DETAILS_UPDATE_PHONE,
            {
               "user_id": 20,
               "mobile_number": data.phone
            },
        ) 
        results = update_mobile_otp
    
    else:
        return {"status": "failure", "message": "Invalid request"}


    return {"status": "success", "message": "OTP verified successfully","data" : results}

@router.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you accessed a protected route!"}








# @router.get("/users")
# def list_users():
#     result = execute_all(USERS_SELECT_ALL)
# pen within a single transaction/connection per request
#     result = await db.read(conn, USERS_SELECT_ALL)






