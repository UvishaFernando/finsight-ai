from pydantic import BaseModel


class CashflowSummary(BaseModel):
    total_income: float
    total_expense: float
    net: float
