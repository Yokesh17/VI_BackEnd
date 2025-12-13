from fastapi import FastAPI, Depends, Request, HTTPException
from db_config import  get_cursor as get_connection, execute_query, insert
from fastapi.responses import JSONResponse
from queries import USERS_TABLE_CREATE, USER_DETAILS_CREATE
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError
from auth import routes as auth_route
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

origins = [
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  "http://127.0.0.1:5500",
  "http://localhost:5500",
  "https://yokesh17.pythonanywhere.com",
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,         # don't use ["*"] if using credentials
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# @app.options("/{rest_of_path:path}")
# async def preflight_handler(rest_of_path: str):
#     return JSONResponse(
#         status_code=200,
#         content=None,
#         headers={
#             "Access-Control-Allow-Origin": "http://localhost:5173",
#             "Access-Control-Allow-Methods": "*",
#             "Access-Control-Allow-Headers": "*",
#             "Access-Control-Allow-Credentials": "true",
#         }
#     )

app.include_router(auth_route.router,tags=["auth"])

# db.register_events(app)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = "; ".join([f"{'.'.join([str(loc) for loc in err['loc']])}: {err['msg']}" for err in errors])

    response = JSONResponse(
        status_code=200,  # or 200 if you prefer
        content={"status": "error", "message": message},
    )
    # Add CORS headers to error response
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )
    # Add CORS headers to error response
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except ValidationError as err:
        response = JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "mandatory fields missing"},
                )
        # Preserve CORS headers for error responses
        origin = request.headers.get("origin")
        if origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
    except Exception as e:
        response = JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": str(e)},
                )
        # Preserve CORS headers for error responses
        origin = request.headers.get("origin")
        if origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

import os
@app.on_event("startup")
def setup_db():
    # Run DDL once at startup; no need for per-request transaction here
    with get_connection() as conn:
        insert(conn,USERS_TABLE_CREATE)
        insert(conn,USER_DETAILS_CREATE)




