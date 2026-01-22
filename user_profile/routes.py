from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request

from utils import get_current_user

from db_config import  get_db_connection as get_connection, get_data, get_datas, execute_query, update, return_update, insert, return_insert, execute_returning_one, execute_all

from .queries import USER_INFO


router = APIRouter(prefix="/profile")


@router.get("/user-info")
def get_user_info(current_user: str = Depends(get_current_user), conn=Depends(get_connection)):
    user_id = current_user["id"]
    result = execute_query(conn, USER_INFO, {"id": user_id})
    if not result:
        return {"status": "failure", "message": "User not found"}
    return {"status": "success", "data": result[0]}


@router.get("/me")
def get_my_profile():
    return {"message": "Get my profile"}












