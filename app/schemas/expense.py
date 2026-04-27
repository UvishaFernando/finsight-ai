from datetime import datetime

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)


class Expense(ExpenseCreate):
    id: int
    created_at: datetime
