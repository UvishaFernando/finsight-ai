from __future__ import annotations

from app.schemas.alerts import Alert, AlertsResponse
from app.services.insights import get_wasteful_habits
from app.services.summary import get_cashflow_summary


def get_alerts(days: int = 7) -> AlertsResponse:
    days = max(1, min(days, 365))

    alerts: list[Alert] = []

    # Alert 1: negative cashflow overall (simple starter rule)
    cashflow = get_cashflow_summary()
    if cashflow.net < 0:
        alerts.append(
            Alert(
                code="NET_NEGATIVE",
                severity="high",
                message="Your net cashflow is negative (expenses > income).",
            )
        )

    # Alert 2: category overspending/frequency signals
    habits = get_wasteful_habits(days=days).habits
    for h in habits:
        alerts.append(
            Alert(
                code=f"WASTEFUL_{h.category.upper()}",
                severity="medium",
                message=h.message,
            )
        )

    return AlertsResponse(days=days, alerts=alerts)
