from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request


router = APIRouter(prefix="/profile")



@router.get("/me")
def get_my_profile():
    return {"message": "Get my profile"}












