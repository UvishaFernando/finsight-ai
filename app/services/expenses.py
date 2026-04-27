from datetime import datetime, timezone

from app.db import get_connection
from app.schemas.expense import Expense, ExpenseCreate


def create_expense(payload: ExpenseCreate) -> Expense:
    created_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses (amount, category, created_at)
            VALUES (?, ?, ?)
            """,
            (payload.amount, payload.category, created_at.isoformat()),
        )
        expense_id = int(cur.lastrowid)

    return Expense(
        id=expense_id,
        amount=payload.amount,
        category=payload.category,
        created_at=created_at,
    )


def list_expenses() -> list[Expense]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, amount, category, created_at
            FROM expenses
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        Expense(
            id=int(row["id"]),
            amount=float(row["amount"]),
            category=str(row["category"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
        for row in rows
    ]
