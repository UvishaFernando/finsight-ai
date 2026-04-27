from datetime import datetime, timezone

from app.db import get_connection
from app.intelligence.expense_categorizer import suggest_category
from app.schemas.expense import Expense, ExpenseCreate
from app.schemas.expense_auto import ExpenseAutoCreate


def create_expense(payload: ExpenseCreate) -> Expense:
    created_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses (amount, category, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (payload.amount, payload.category, payload.description, created_at.isoformat()),
        )
        expense_id = int(cur.lastrowid)

    return Expense(
        id=expense_id,
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        created_at=created_at,
    )


def create_expense_auto(payload: ExpenseAutoCreate) -> Expense:
    category = suggest_category(payload.description)
    return create_expense(
        ExpenseCreate(
            amount=payload.amount,
            category=category,
            description=payload.description,
        )
    )


def list_expenses() -> list[Expense]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, amount, category, description, created_at
            FROM expenses
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        Expense(
            id=int(row["id"]),
            amount=float(row["amount"]),
            category=str(row["category"]),
            description=row["description"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
        for row in rows
    ]
