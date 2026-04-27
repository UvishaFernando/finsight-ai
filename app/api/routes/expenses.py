from fastapi import APIRouter

from app.intelligence.expense_categorizer import suggest_category
from app.schemas.categorization import (
    CategorySuggestionRequest,
    CategorySuggestionResponse,
)
from app.schemas.expense import Expense, ExpenseCreate
from app.schemas.expense_auto import ExpenseAutoCreate
from app.services.expenses import create_expense, create_expense_auto, list_expenses

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=Expense)
def post_expense(payload: ExpenseCreate) -> Expense:
    return create_expense(payload)


@router.post("/auto", response_model=Expense)
def post_expense_auto(payload: ExpenseAutoCreate) -> Expense:
    return create_expense_auto(payload)


@router.get("", response_model=list[Expense])
def get_expenses() -> list[Expense]:
    return list_expenses()


@router.post("/suggest-category", response_model=CategorySuggestionResponse)
def suggest_expense_category(
    payload: CategorySuggestionRequest,
) -> CategorySuggestionResponse:
    return CategorySuggestionResponse(category=suggest_category(payload.text))
