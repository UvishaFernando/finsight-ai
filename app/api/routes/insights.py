from fastapi import APIRouter, Query

from app.schemas.insights import WastefulHabitsResponse
from app.services.insights import get_wasteful_habits

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/wasteful-habits", response_model=WastefulHabitsResponse)
def wasteful_habits(days: int = Query(7, ge=1, le=365)) -> WastefulHabitsResponse:
    return get_wasteful_habits(days=days)
