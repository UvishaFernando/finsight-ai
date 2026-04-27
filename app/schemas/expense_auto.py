from pydantic import BaseModel, Field


class ExpenseAutoCreate(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=200)
