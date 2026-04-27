from fastapi import APIRouter, Query

from app.schemas.score import FinancialHealthScore
from app.services.score import get_financial_health_score

router = APIRouter(prefix="/score", tags=["score"])


@router.get("/financial-health", response_model=FinancialHealthScore)
def financial_health(days: int = Query(30, ge=1, le=365)) -> FinancialHealthScore:
    return get_financial_health_score(days=days)
