from fastapi import FastAPI, Depends, Request
from db_config import db, get_connection
from fastapi.responses import JSONResponse
import users
from queries import USERS_TABLE_CREATE

app = FastAPI()
app.include_router(users.app,tags=["users"])

db.register_events(app)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
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




