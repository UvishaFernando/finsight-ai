from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="FinSight AI")

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)


class Expense(ExpenseCreate):
    id: int
    created_at: datetime


_expenses: list[Expense] = []
_next_id = 1


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/expenses", response_model=Expense)
def create_expense(payload: ExpenseCreate) -> Expense:
    global _next_id

    expense = Expense(
        id=_next_id,
        amount=payload.amount,
        category=payload.category,
        created_at=datetime.now(timezone.utc),
    )

    _next_id += 1
    _expenses.append(expense)
    return expense


@app.get("/expenses", response_model=list[Expense])
def list_expenses() -> list[Expense]:
    return _expenses
