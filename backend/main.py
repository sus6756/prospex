from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from models import Company, Contact, ICP, Lead, User  # noqa: F401
from routers import auth, chat, icp, leads, discovery, export

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Prospex — Lead Discovery & Qualification Platform",
    version="1.0.0",
    description="Prospex: AI-powered B2B lead discovery and qualification API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    return {"status": "healthy", "env": settings.ENV}