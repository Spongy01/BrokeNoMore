from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from models import PasswordResetToken, Transaction, User, UserThread  # noqa: F401 — register all tables
from routers import transactions, query
from routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="BrokeNoMore API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(transactions.router)
app.include_router(query.router)


@app.get("/")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
