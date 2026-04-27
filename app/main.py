from fastapi import FastAPI

from app.api.routes.expenses import router as expenses_router
from app.api.routes.incomes import router as incomes_router
from app.api.routes.insights import router as insights_router
from app.api.routes.score import router as score_router
from app.api.routes.summary import router as summary_router
from app.db import init_db

app = FastAPI(title="FinSight AI", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(expenses_router)
app.include_router(incomes_router)
app.include_router(summary_router)
app.include_router(insights_router)
app.include_router(score_router)
