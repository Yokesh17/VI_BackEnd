from fastapi import APIRouter, Depends, Request
from db_config import db, get_connection
from pydantic import BaseModel, EmailStr, Field
from queries import  USERS_SELECT_ALL, USERS_INSERT

app = APIRouter()


class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  
    email: EmailStr  # Validates if the email is in a valid format
    password: str = Field(..., min_length=8) 


@app.get("/users")
async def list_users(conn=Depends(get_connection)):
    # Both queries happen within a single transaction/connection per request
    result = await db.read(conn, USERS_SELECT_ALL)
    return {"status" : "success" , "data" : result }


@app.post("/signUp")
async def create_user(data : User, conn=Depends(get_connection)):
    result = await db.insert(
        conn,
        USERS_INSERT,
        {"username": data.username, "email": data.email, "password": data.password},
    )
    return {"status" : "success","data": result }



