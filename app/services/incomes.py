from datetime import datetime, timezone

from app.db import get_connection
from app.schemas.income import Income, IncomeCreate


def create_income(payload: IncomeCreate) -> Income:
    created_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO incomes (amount, source, created_at)
            VALUES (?, ?, ?)
            """,
            (payload.amount, payload.source, created_at.isoformat()),
        )
        income_id = int(cur.lastrowid)

    return Income(
        id=income_id,
        amount=payload.amount,
        source=payload.source,
        created_at=created_at,
    )


def list_incomes() -> list[Income]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, amount, source, created_at
            FROM incomes
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        Income(
            id=int(row["id"]),
            amount=float(row["amount"]),
            source=str(row["source"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
        for row in rows
    ]
