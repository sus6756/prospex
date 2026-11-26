import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import database_status, init_db
from models import Company, Contact, ICP, Lead, User  # noqa: F401
from routers import auth, chat, icp, leads, discovery, export

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

init_db()

app = FastAPI(
    title="Prospex — Lead Discovery & Qualification Platform",
    version="1.0.0",
    description="Prospex: AI-powered B2B lead discovery and qualification API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(icp.router)
app.include_router(leads.router)
app.include_router(discovery.router)
app.include_router(export.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "status": "ok", "version": "1.0.0"}


@app.get("/api/health")
def health():
    db = database_status()
    return {
        "status": "healthy" if db["connected"] else "degraded",
        "env": settings.ENV,
        "database": db,
    }