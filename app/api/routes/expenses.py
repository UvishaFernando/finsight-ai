from fastapi import APIRouter

from app.schemas.expense import Expense, ExpenseCreate
from app.services.expenses import create_expense, list_expenses

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=Expense)
def post_expense(payload: ExpenseCreate) -> Expense:
    return create_expense(payload)


@router.get("", response_model=list[Expense])
def get_expenses() -> list[Expense]:
    return list_expenses()
