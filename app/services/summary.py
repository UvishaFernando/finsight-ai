from app.db import get_connection
from app.schemas.summary import CashflowSummary


def get_cashflow_summary() -> CashflowSummary:
    with get_connection() as conn:
        income_row = conn.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM incomes").fetchone()
        expense_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        ).fetchone()

    total_income = float(income_row["total"])
    total_expense = float(expense_row["total"])
    return CashflowSummary(
        total_income=total_income,
        total_expense=total_expense,
        net=total_income - total_expense,
    )
