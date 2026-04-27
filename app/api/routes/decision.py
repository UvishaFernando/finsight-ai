from fastapi import APIRouter

from app.schemas.decision import BuyWaitRequest, BuyWaitResponse
from app.services.decision import buy_now_or_wait

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/buy-wait", response_model=BuyWaitResponse)
def buy_wait(payload: BuyWaitRequest) -> BuyWaitResponse:
    return buy_now_or_wait(payload)
