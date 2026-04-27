from fastapi import APIRouter, Query

from app.schemas.alerts import AlertsResponse
from app.services.alerts import get_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertsResponse)
def alerts(days: int = Query(7, ge=1, le=365)) -> AlertsResponse:
    return get_alerts(days=days)
