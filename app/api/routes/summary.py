from fastapi import APIRouter

from app.schemas.summary import CashflowSummary
from app.services.summary import get_cashflow_summary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/cashflow", response_model=CashflowSummary)
def cashflow_summary() -> CashflowSummary:
    return get_cashflow_summary()
