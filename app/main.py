from fastapi import FastAPI

from app.api.routes.expenses import router as expenses_router
from app.db import init_db

app = FastAPI(title="FinSight AI", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(expenses_router)
