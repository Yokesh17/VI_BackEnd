from fastapi import APIRouter, Depends,Path, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from utils import  decode_token
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, BaseModel
from typing import Union, Literal, List, Dict
import base64
import json
from datetime import datetime, date

from .query import SUGGESTION_QUERY    

from db_config import  get_db_connection as get_connection, get_data, get_datas, execute_query, update, return_update, insert, return_insert, execute_returning_one, execute_all

from utils import get_current_user

router = APIRouter(prefix="/suggestions")

@router.get("/friends/{limit}")
def fetch_friend_suggestions(
    limit: int = Path(gt=0, le=50),
    conn =Depends(get_connection),
    user_id = Depends(get_current_user)
):
    suggestions = get_friend_suggestions(
        conn=conn,
        current_user_id=user_id[0]["id"],
        limit=limit
    )

    if not suggestions: return {"message": "No suggestions found"}

    return {"status" : "success","count": len(suggestions), "data": suggestions  }

def get_friend_suggestions(
        conn,
        current_user_id: int,
        limit: int = 10
    ):

    params = {
                "current_user_id": current_user_id,
                "limit": limit
            }
    result = execute_query(conn, SUGGESTION_QUERY,params)
    
    return result









