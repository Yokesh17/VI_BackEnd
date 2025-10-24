from fastapi import FastAPI, Depends, Request
from db_config import db, get_connection
from fastapi.responses import JSONResponse

app = FastAPI()
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
        await db.insert(
            conn,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT
            )
            """,
        )


@app.get("/users")
async def list_users(conn=Depends(get_connection)):
    # Both queries happen within a single transaction/connection per request
    result = await db.read(conn, "SELECT * FROM users")
    return {"status" : "success" , "data" : result }


@app.post("/users")
async def create_user(name: str, email: str, conn=Depends(get_connection)):
    await db.insert(
        conn,
        "INSERT INTO users (name, email) VALUES (:name, :email)",
        {"name": name, "email": email},
    )
    return {"message": "User added"}