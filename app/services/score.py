from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db import get_connection
from app.schemas.score import FinancialHealthScore
from app.services.insights import get_wasteful_habits


def _clamp_int(x: float, lo: int, hi: int) -> int:
    return max(lo, min(int(round(x)), hi))


def _level(score: int) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def get_financial_health_score(days: int = 30) -> FinancialHealthScore:
    days = max(1, min(days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with get_connection() as conn:
        income_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM incomes WHERE created_at >= ?",
            (cutoff.isoformat(),),
        ).fetchone()
        expense_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE created_at >= ?",
            (cutoff.isoformat(),),
        ).fetchone()

    total_income = float(income_row["total"])
    total_expense = float(expense_row["total"])
    net = total_income - total_expense

    # savings_rate is how much of income remains.
    savings_rate = (net / total_income) if total_income > 0 else 0.0
    savings_rate = max(0.0, min(savings_rate, 1.0))

    # Base score: rewards saving, penalizes high spending ratio.
    # - savings_rate 0.0 => 0 points, 1.0 => 70 points
    # - spending_ratio 0.0 => 30 points, 1.0+ => 0 points
    spending_ratio = (total_expense / total_income) if total_income > 0 else 1.0
    saving_points = savings_rate * 70.0
    spending_points = max(0.0, 30.0 - (min(spending_ratio, 1.0) * 30.0))
    base_score = saving_points + spending_points

    # Habit penalty: each detected habit reduces score a bit (max 15).
    habits = get_wasteful_habits(days=days).habits
    habit_penalty = min(15, len(habits) * 5)

    score = _clamp_int(base_score - habit_penalty, 0, 100)

    return FinancialHealthScore(
        days=days,
        score=score,
        level=_level(score),
        total_income=total_income,
        total_expense=total_expense,
        net=net,
        savings_rate=savings_rate,
        habit_penalty=habit_penalty,
    )
