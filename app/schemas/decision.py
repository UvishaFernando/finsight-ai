from pydantic import BaseModel, Field


class BuyWaitRequest(BaseModel):
    item: str = Field(..., min_length=1, max_length=50)
    current_price: float = Field(..., gt=0)
    horizon_days: int = Field(..., ge=1, le=30)  # 3, 7, 30 are common
    risk_level: str = Field("medium", pattern="^(low|medium|high)$")


class BuyWaitResponse(BaseModel):
    item: str
    current_price: float
    predicted_price: float
    horizon_days: int
    action: str  # "BUY_NOW" | "WAIT"
    risk_level: str
    reason: str
