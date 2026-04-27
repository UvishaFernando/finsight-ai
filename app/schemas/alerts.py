from pydantic import BaseModel


class Alert(BaseModel):
    code: str
    severity: str  # "low" | "medium" | "high"
    message: str


class AlertsResponse(BaseModel):
    days: int
    alerts: list[Alert]
