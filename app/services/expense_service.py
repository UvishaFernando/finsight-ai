"""
Expense Service
===============
All business logic for creating, reading, updating, and deleting
expenses and budgets. Keeps the endpoint layer thin.
"""

from decimal import Decimal
from typing import Optional
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from fastapi import HTTPException, status

from app.models.expense import Expense, Budget, ExpenseCategory, TransactionType
from app.models.user import User
from app.services.categorizer import categorize
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, BudgetCreate,
    MonthlySummary, CategoryBreakdown,
)


class ExpenseService:

    # ── CREATE ────────────────────────────────────────────────────────────────

    @staticmethod
    def create_expense(db: Session, user: User, data: ExpenseCreate) :
        """
        Create a new expense. If category is not provided, the
        auto-categorization AI fills it in automatically.

        Returns (expense, categorization_reason)
        """
        categorization_reason = None
        auto_categorized = False
        confidence = Decimal("1.00")

        # If user didn't provide a category → run the AI categorizer
        category = data.category
        tx_type = data.transaction_type

        if category is None:
            result = categorize(data.description)
            category = result.category
            tx_type = result.transaction_type
            confidence = Decimal(str(result.confidence))
            categorization_reason = result.reasoning
            auto_categorized = True

        # If type still missing, infer from category
        if tx_type is None:
            income_cats = {
                ExpenseCategory.salary, ExpenseCategory.freelance,
                ExpenseCategory.business_income, ExpenseCategory.other_income,
            }
            tx_type = TransactionType.income if category in income_cats else TransactionType.expense

        expense = Expense(
            user_id=user.id,
            amount=data.amount,
            description=data.description,
            raw_description=data.description,
            category=category,
            transaction_type=tx_type,
            transaction_date=data.transaction_date,
            auto_categorized=auto_categorized,
            categorization_confidence=confidence,
            notes=data.notes,
            is_recurring=data.is_recurring,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense, categorization_reason

    # ── READ ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_expense(db: Session, user: User, expense_id: int) :
        expense = db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user.id
        ).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense {expense_id} not found"
            )
        return expense

    @staticmethod
    def list_expenses(
        db: Session,
        user: User,
        month: Optional[int] = None,
        year: Optional[int] = None,
        category: Optional[ExpenseCategory] = None,
        transaction_type: Optional[TransactionType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Expense], int]:
        """
        List expenses with optional filters. Returns (expenses, total_count).
        Paginated — page 1 is the default.
        """
        query = db.query(Expense).filter(Expense.user_id == user.id)

        if month:
            query = query.filter(extract("month", Expense.transaction_date) == month)
        if year:
            query = query.filter(extract("year", Expense.transaction_date) == year)
        if category:
            query = query.filter(Expense.category == category)
        if transaction_type:
            query = query.filter(Expense.transaction_type == transaction_type)

        total = query.count()
        expenses = (
            query
            .order_by(Expense.transaction_date.desc(), Expense.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return expenses, total

    # ── UPDATE ────────────────────────────────────────────────────────────────

    @staticmethod
    def update_expense(
        db: Session, user: User, expense_id: int, data: ExpenseUpdate
    ) -> Expense:
        expense = ExpenseService.get_expense(db, user, expense_id)

        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(expense, field, value)

        # If description changed and category was auto-set, re-categorize
        if "description" in updates and expense.auto_categorized and "category" not in updates:
            result = categorize(updates["description"])
            expense.category = result.category
            expense.transaction_type = result.transaction_type
            expense.categorization_confidence = Decimal(str(result.confidence))

        db.commit()
        db.refresh(expense)
        return expense

    # ── DELETE ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_expense(db: Session, user: User, expense_id: int) -> None:
        expense = ExpenseService.get_expense(db, user, expense_id)
        db.delete(expense)
        db.commit()

    # ── ANALYTICS ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_monthly_summary(db: Session, user: User, month: int, year: int) -> MonthlySummary:
        """
        Full breakdown of a user's month:
        - Total income vs expenses
        - Net balance and savings rate
        - Spending by category with percentages
        """
        expenses, _ = ExpenseService.list_expenses(
            db, user, month=month, year=year, page_size=10000
        )

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        category_totals: dict[ExpenseCategory, tuple[Decimal, int]] = defaultdict(
            lambda: (Decimal("0"), 0)
        )

        for e in expenses:
            if e.transaction_type == TransactionType.income:
                total_income += e.amount
            else:
                total_expenses += e.amount
                prev_total, prev_count = category_totals[e.category]
                category_totals[e.category] = (prev_total + e.amount, prev_count + 1)

        net_balance = total_income - total_expenses
        savings_rate = 0.0
        if total_income > 0:
            savings_rate = round(float(net_balance / total_income) * 100, 1)

        breakdown = []
        for cat, (total, count) in sorted(
            category_totals.items(), key=lambda x: x[1][0], reverse=True
        ):
            pct = round(float(total / total_expenses) * 100, 1) if total_expenses > 0 else 0.0
            breakdown.append(CategoryBreakdown(
                category=cat,
                total=total,
                count=count,
                percentage=pct,
            ))

        return MonthlySummary(
            month=month,
            year=year,
            total_income=total_income,
            total_expenses=total_expenses,
            net_balance=net_balance,
            savings_rate=savings_rate,
            transaction_count=len(expenses),
            category_breakdown=breakdown,
        )

    # ── BUDGETS ───────────────────────────────────────────────────────────────

    @staticmethod
    def set_budget(db: Session, user: User, data: BudgetCreate) -> Budget:
        """Create or update a budget for a category/month/year."""
        existing = db.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.category == data.category,
            Budget.month == data.month,
            Budget.year == data.year,
        ).first()

        if existing:
            existing.monthly_limit = data.monthly_limit
            db.commit()
            db.refresh(existing)
            return existing

        budget = Budget(
            user_id=user.id,
            category=data.category,
            monthly_limit=data.monthly_limit,
            month=data.month,
            year=data.year,
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def get_budgets_with_spending(
        db: Session, user: User, month: int, year: int
    ) -> list[dict]:
        """
        Returns budgets enriched with actual spending data.
        Shows how much of each budget has been used.
        """
        budgets = db.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.month == month,
            Budget.year == year,
        ).all()

        result = []
        for budget in budgets:
            spent = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user.id,
                Expense.category == budget.category,
                Expense.transaction_type == TransactionType.expense,
                extract("month", Expense.transaction_date) == month,
                extract("year", Expense.transaction_date) == year,
            ).scalar() or Decimal("0")

            remaining = budget.monthly_limit - spent
            usage_pct = round(float(spent / budget.monthly_limit) * 100, 1) \
                if budget.monthly_limit > 0 else 0.0

            result.append({
                "budget": budget,
                "spent_so_far": spent,
                "remaining": remaining,
                "usage_percent": usage_pct,
            })

        return result
