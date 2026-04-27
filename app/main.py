from fastapi import FastAPI

app = FastAPI(title="FinSight AI", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
