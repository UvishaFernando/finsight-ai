from pydantic import BaseModel


class WastefulHabit(BaseModel):
    category: str
    total_amount: float
    transaction_count: int
    message: str


class WastefulHabitsResponse(BaseModel):
    days: int
    habits: list[WastefulHabit]
