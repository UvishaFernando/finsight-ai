from fastapi import FastAPI

from app.api.routes.decision import router as decision_router

app = FastAPI(title="FinSight AI", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(decision_router)
