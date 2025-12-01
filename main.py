from fastapi import FastAPI, Depends, Request, HTTPException
from db_config import db, get_connection
from fastapi.responses import JSONResponse
from queries import USERS_TABLE_CREATE
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError
from auth import routes as auth_route
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173/","http://127.0.0.1:5500/","http://127.0.0.1:5500/test.html"],            # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all request headers
)


app.include_router(auth_route.router,tags=["auth"])

db.register_events(app)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = "; ".join([f"{'.'.join([str(loc) for loc in err['loc']])}: {err['msg']}" for err in errors])

    return JSONResponse(
        status_code=200,  # or 200 if you prefer
        content={"status": "error", "message": message},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except ValidationError as err:
        response = JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "mandatory fields missing"},
                )
    except Exception as e:
        response = JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": str(e)},
                )
    return response


@app.on_event("startup")
async def setup_db():
    # Run DDL once at startup; no need for per-request transaction here
    async with db.connection() as conn:
        await db.insert(conn,USERS_TABLE_CREATE)




