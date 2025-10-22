from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def middleware(request : Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        response = {"status" : "error", "message" : str(e)}
    return response


@app.get("/new")
def new():
    return "we are working"