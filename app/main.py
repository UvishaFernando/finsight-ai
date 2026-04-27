from fastapi import FastAPI

from app.api.routes.expenses import router as expenses_router

app = FastAPI(title="FinSight AI", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(expenses_router)
