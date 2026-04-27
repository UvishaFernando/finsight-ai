from datetime import datetime

from pydantic import BaseModel, Field


class IncomeCreate(BaseModel):
    amount: float = Field(..., gt=0)
    source: str = Field(..., min_length=1, max_length=50)


class Income(IncomeCreate):
    id: int
    created_at: datetime
