from __future__ import annotations

from app.schemas.decision import BuyWaitRequest, BuyWaitResponse


def _get_daily_increase_rate(item: str) -> float:
    """
    Simple starter assumptions.
    Later we'll replace this with real market data + forecasting models.
    """
    key = item.strip().lower()
    rates = {
        "rice": 0.0015,  # +0.15% per day
        "fuel": 0.0025,  # +0.25% per day
        "electricity": 0.0010,  # +0.10% per day
    }
    return rates.get(key, 0.0012)


def _threshold_for_risk(risk_level: str) -> float:
    # How much increase is "enough" to justify buying now.
    # low risk => smaller threshold (more likely BUY_NOW)
    # high risk => larger threshold (more likely WAIT)
    return {"low": 0.01, "medium": 0.03, "high": 0.05}[risk_level]


def buy_now_or_wait(req: BuyWaitRequest) -> BuyWaitResponse:
    daily_rate = _get_daily_increase_rate(req.item)
    predicted_price = req.current_price * (1.0 + (daily_rate * req.horizon_days))

    increase_pct = (predicted_price - req.current_price) / req.current_price
    threshold = _threshold_for_risk(req.risk_level)

    if increase_pct >= threshold:
        action = "BUY_NOW"
        reason = (
            f"Predicted price increase is about {increase_pct:.1%} in {req.horizon_days} days, "
            f"which is above your {req.risk_level} risk threshold ({threshold:.0%})."
        )
    else:
        action = "WAIT"
        reason = (
            f"Predicted price increase is about {increase_pct:.1%} in {req.horizon_days} days, "
            f"which is below your {req.risk_level} risk threshold ({threshold:.0%})."
        )

    return BuyWaitResponse(
        item=req.item,
        current_price=req.current_price,
        predicted_price=round(predicted_price, 2),
        horizon_days=req.horizon_days,
        action=action,
        risk_level=req.risk_level,
        reason=reason,
    )
