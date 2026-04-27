from datetime import datetime, timezone

from app.schemas.expense import Expense, ExpenseCreate

_expenses: list[Expense] = []
_next_id = 1


def create_expense(payload: ExpenseCreate) -> Expense:
    global _next_id

    expense = Expense(
        id=_next_id,
        amount=payload.amount,
        category=payload.category,
        created_at=datetime.now(timezone.utc),
    )

    _next_id += 1
    _expenses.append(expense)
    return expense


def list_expenses() -> list[Expense]:
    return _expenses
