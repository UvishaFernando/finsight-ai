"""
Wasteful Habit Detector
========================
Analyzes spending patterns and flags categories where the user is
overspending compared to their own historical average.

No external data needed — compares the user against themselves.
Output is actionable: specific category, amount over, and a saving tip.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.models.expense import Expense, ExpenseCategory, TransactionType
from app.services.categorizer import is_potentially_wasteful, is_essential
from app.schemas.expense import WasteAlert, WasteReport


# ── Thresholds ────────────────────────────────────────────────────────────────

OVERSPEND_THRESHOLD_PCT = 20.0   # flag if 20%+ above personal average
MIN_MONTHS_FOR_ANALYSIS = 1      # need at least 1 prior month of data
MIN_TRANSACTIONS = 2             # ignore categories with < 2 transactions


# ── Saving Tips per Category ──────────────────────────────────────────────────

SAVING_TIPS: dict[ExpenseCategory, str] = {
    ExpenseCategory.restaurants:       "Cook at home 3 extra days a week — saves Rs. 3,000-5,000/month on average.",
    ExpenseCategory.street_food:       "Carry homemade snacks. A packed lunch saves Rs. 500-800 per week.",
    ExpenseCategory.entertainment:     "Share streaming subscriptions with family. Cancel unused services.",
    ExpenseCategory.clothing:          "Try the 30-day rule: wait 30 days before buying non-essential clothing.",
    ExpenseCategory.transport_rideshare: "Use CTB/private bus for regular routes. Save PickMe for late nights only.",
    ExpenseCategory.transport_fuel:    "Combine errands into one trip. Check tyre pressure monthly for fuel efficiency.",
    ExpenseCategory.supermarket:       "Switch to pola for vegetables and fruits — typically 30-50% cheaper.",
    ExpenseCategory.mobile_dialog:     "Review your data plan. Downgrade if you consistently have unused data.",
    ExpenseCategory.mobile_mobitel:    "Review your data plan. Downgrade if you consistently have unused data.",
    ExpenseCategory.internet:          "Check if your current plan matches actual usage. Downgrade if overprovisioned.",
    ExpenseCategory.food_groceries:    "Make a weekly shopping list before going to the market. Avoid impulse buys.",
    ExpenseCategory.pola_market:       "Visit pola early morning for fresh produce at lower prices.",
}

DEFAULT_TIP = "Review this category's spending and identify non-essential items to cut."


def _severity(overspend_pct: float) -> str:
    if overspend_pct >= 50:
        return "high"
    if overspend_pct >= 30:
        return "medium"
    return "low"


def analyze_waste(db: Session, user_id: int) -> WasteReport:
    """
    Main function. Analyzes the last 30 days vs the 90 days before that.

    Algorithm:
      1. Get current month spending by category
      2. Get average of previous 3 months by category
      3. Flag categories 20%+ above their own average
      4. Return ranked alerts with tips
    """
    today = date.today()
    current_month_start = today.replace(day=1)
    three_months_ago = (current_month_start - timedelta(days=90)).replace(day=1)

    # Current month spending by category
    current_rows = (
        db.query(Expense.category, Expense.amount)
        .filter(
            Expense.user_id == user_id,
            Expense.transaction_type == TransactionType.expense,
            Expense.transaction_date >= current_month_start,
            Expense.transaction_date <= today,
        )
        .all()
    )

    current_spending: dict[ExpenseCategory, Decimal] = defaultdict(Decimal)
    current_count: dict[ExpenseCategory, int] = defaultdict(int)
    for cat, amount in current_rows:
        current_spending[cat] += amount
        current_count[cat] += 1

    # Previous 3 months spending by category
    prev_rows = (
        db.query(Expense.category, Expense.amount)
        .filter(
            Expense.user_id == user_id,
            Expense.transaction_type == TransactionType.expense,
            Expense.transaction_date >= three_months_ago,
            Expense.transaction_date < current_month_start,
        )
        .all()
    )

    prev_spending: dict[ExpenseCategory, Decimal] = defaultdict(Decimal)
    for cat, amount in prev_rows:
        prev_spending[cat] += amount

    # Build alerts
    alerts: list[WasteAlert] = []
    total_potential_savings = Decimal("0")

    for cat, this_month in current_spending.items():
        if current_count[cat] < MIN_TRANSACTIONS:
            continue

        if cat not in prev_spending or prev_spending[cat] == 0:
            continue  # no historical data for this category

        # Average previous 3 months (divide by 3)
        avg_prev = prev_spending[cat] / Decimal("3")
        if avg_prev == 0:
            continue

        overspend_pct = float((this_month - avg_prev) / avg_prev) * 100

        if overspend_pct >= OVERSPEND_THRESHOLD_PCT:
            overspend_amount = this_month - avg_prev
            total_potential_savings += overspend_amount
            severity = _severity(overspend_pct)

            alerts.append(WasteAlert(
                category=cat,
                this_month=this_month,
                avg_previous_months=avg_prev.quantize(Decimal("0.01")),
                overspend_percent=round(overspend_pct, 1),
                overspend_amount=overspend_amount.quantize(Decimal("0.01")),
                severity=severity,
                message=(
                    f"Your {cat.value.replace('_', ' ')} spending is "
                    f"{overspend_pct:.0f}% higher than your 3-month average. "
                    f"You spent Rs. {this_month:,.0f} vs your usual Rs. {avg_prev:,.0f}."
                ),
                tip=SAVING_TIPS.get(cat, DEFAULT_TIP),
            ))

    # Sort by overspend amount — biggest waste first
    alerts.sort(key=lambda a: a.overspend_amount, reverse=True)

    if alerts:
        summary = (
            f"Found {len(alerts)} spending category{'s' if len(alerts) > 1 else ''} "
            f"above your personal average. "
            f"Reducing these could save you Rs. {total_potential_savings:,.0f} this month."
        )
    else:
        summary = "Your spending looks consistent with your historical patterns. Well done!"

    return WasteReport(
        analysis_period_days=30,
        alerts=alerts,
        total_potential_savings=total_potential_savings.quantize(Decimal("0.01")),
        summary=summary,
    )
