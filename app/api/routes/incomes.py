from fastapi import APIRouter

from app.schemas.income import Income, IncomeCreate
from app.services.incomes import create_income, list_incomes

router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.post("", response_model=Income)
def post_income(payload: IncomeCreate) -> Income:
    return create_income(payload)


@router.get("", response_model=list[Income])
def get_incomes() -> list[Income]:
    return list_incomes()
