from pydantic import BaseModel


class FinancialHealthScore(BaseModel):
    days: int
    score: int  # 0..100
    level: str  # "poor" | "fair" | "good" | "excellent"

    total_income: float
    total_expense: float
    net: float
    savings_rate: float  # 0..1 (net / income), 0 if income is 0

    habit_penalty: int
