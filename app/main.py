from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.base import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print(f"✅ FinSight AI started — {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    print("🔴 FinSight AI shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## FinSight AI — Sri Lanka Financial Intelligence System

An AI-powered personal finance platform built specifically for Sri Lanka.

### Features (MVP)
- 🔐 JWT Authentication with bcrypt password hashing
- 💸 Expense tracking with auto-categorization
- 📊 Financial health score (0–100)
- 🚨 Smart alerts for overspending
- 🇱🇰 Sri Lanka market price dashboard

### Auth Flow
1. `POST /api/v1/auth/register` — create account
2. `POST /api/v1/auth/login` — get access + refresh tokens
3. Add `Authorization: Bearer <access_token>` to all protected requests
4. `POST /api/v1/auth/refresh` — get new access token when expired
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}
