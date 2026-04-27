from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.db import get_connection
from app.schemas.insights import WastefulHabit, WastefulHabitsResponse


def get_wasteful_habits(days: int = 7) -> WastefulHabitsResponse:
    # Keep rules simple and readable for beginners.
    # We can evolve these rules later (per-user budgets, ML, etc.).
    days = max(1, min(days, 365))

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT amount, category, created_at
            FROM expenses
            WHERE created_at >= ?
            """,
            (cutoff.isoformat(),),
        ).fetchall()

    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)

    for row in rows:
        category = str(row["category"])
        totals[category] += float(row["amount"])
        counts[category] += 1

    habits: list[WastefulHabit] = []

    # Very basic rule thresholds (adjust later):
    spend_thresholds = {
        "transport": 5000.0,
        "food": 8000.0,
        "entertainment": 3000.0,
    }
    frequency_thresholds = {
        "transport": 10,
        "food": 12,
        "entertainment": 6,
    }

    for category, total in totals.items():
        count = counts[category]

        spend_limit = spend_thresholds.get(category)
        freq_limit = frequency_thresholds.get(category)

        if spend_limit is not None and total >= spend_limit:
            habits.append(
                WastefulHabit(
                    category=category,
                    total_amount=total,
                    transaction_count=count,
                    message=f"High spending in '{category}' over last {days} days.",
                )
            )
            continue

        if freq_limit is not None and count >= freq_limit:
            habits.append(
                WastefulHabit(
                    category=category,
                    total_amount=total,
                    transaction_count=count,
                    message=f"Frequent spending in '{category}' over last {days} days.",
                )
            )

    # Sort biggest impact first.
    habits.sort(key=lambda h: h.total_amount, reverse=True)

    return WastefulHabitsResponse(days=days, habits=habits)
