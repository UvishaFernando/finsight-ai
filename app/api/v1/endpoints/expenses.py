"""
Expense Endpoints
=================
Clean, thin endpoint layer — all logic lives in ExpenseService.
Every route is protected by JWT (get_current_active_user dependency).
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.db.base import get_db
from app.models.user import User
from app.models.expense import ExpenseCategory, TransactionType
from app.api.v1.dependencies import get_current_active_user
from app.services.expense_service import ExpenseService
from app.services.waste_detector import analyze_waste
from app.services.categorizer import categorize
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse,BudgetCreate, BudgetResponse,MonthlySummary, WasteReport, CategorizationPreview
from app.schemas.user import MessageResponse

router = APIRouter(prefix="/expenses", tags=["Expenses & Budgets"])


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new transaction (AI auto-categorizes if no category given)",
)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add an income or expense transaction.

    **AI Auto-categorization:** If you don't provide `category`, the engine
    will automatically detect it from the description using the Sri Lanka
    keyword dictionary.

    Examples:
    - `"Keells supermarket weekly shopping"` → `supermarket`
    - `"CEB electricity bill"` → `electricity_ceb`
    - `"Dialog reload 200"` → `mobile_dialog`
    - `"Monthly salary"` → `salary` (income)

    The response includes `auto_categorized` and `categorization_reason`
    so you can see exactly why the AI chose that category.
    """
    expense, reason = ExpenseService.create_expense(db, current_user, data)
    response = ExpenseResponse.model_validate(expense)
    response.categorization_reason = reason
    return response


# ── READ (list) ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=ExpenseListResponse,
    summary="List transactions with optional filters",
)
def list_expenses(
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, ge=2020, description="Filter by year"),
    category: Optional[ExpenseCategory] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all your transactions. Supports filtering by month, year,
    category, and transaction type. Paginated.
    """
    expenses, total = ExpenseService.list_expenses(
        db, current_user,
        month=month, year=year,
        category=category, transaction_type=transaction_type,
        page=page, page_size=page_size,
    )
    return ExpenseListResponse(
        expenses=[ExpenseResponse.model_validate(e) for e in expenses],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


# ── READ (single) ─────────────────────────────────────────────────────────────

@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get a single transaction by ID",
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    expense = ExpenseService.get_expense(db, current_user, expense_id)
    return ExpenseResponse.model_validate(expense)


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update a transaction",
)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update any field of a transaction. Only provided fields are updated.
    If description changes and the transaction was auto-categorized,
    the AI will re-categorize it automatically.
    """
    expense = ExpenseService.update_expense(db, current_user, expense_id, data)
    return ExpenseResponse.model_validate(expense)


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{expense_id}",
    response_model=MessageResponse,
    summary="Delete a transaction",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ExpenseService.delete_expense(db, current_user, expense_id)
    return MessageResponse(message=f"Transaction {expense_id} deleted successfully")


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

@router.get(
    "/analytics/monthly-summary",
    response_model=MonthlySummary,
    summary="Get full monthly income/expense breakdown",
)
def monthly_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1–12)"),
    year: int = Query(..., ge=2020, description="Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Complete monthly financial summary:
    - Total income vs expenses
    - Net balance and savings rate
    - Spending breakdown by category with percentages

    This powers the main dashboard charts.
    """
    return ExpenseService.get_monthly_summary(db, current_user, month, year)


@router.get(
    "/analytics/waste-detection",
    response_model=WasteReport,
    summary="AI waste detector — find your overspending categories",
)
def waste_detection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyzes your spending patterns and flags categories where you are
    spending significantly more than your personal historical average.

    **How it works:**
    - Compares current month spending vs your 3-month average per category
    - Flags any category 20%+ above your own average
    - Provides specific, actionable Sri Lanka saving tips

    Example output:
    - "Your restaurant spending is 45% above your 3-month average"
    - "Switch to pola for vegetables — typically 30–50% cheaper"
    """
    return analyze_waste(db, current_user.id)


@router.post(
    "/ai/preview-category",
    response_model=CategorizationPreview,
    summary="Preview what category the AI would assign — without saving",
)
def preview_category(
    description: str = Query(..., description="Transaction description to categorize"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Test the auto-categorization engine on any description.
    Useful for the frontend to show a live category preview as the user types.

    Examples to try:
    - "Keells supermarket"
    - "CEB electricity bill April"
    - "PickMe to Colombo"
    - "Monthly salary"
    - "Nawaloka hospital"
    """
    result = categorize(description)
    return CategorizationPreview(
        description=description,
        suggested_category=result.category,
        suggested_type=result.transaction_type,
        confidence=result.confidence,
        matched_keyword=result.matched_keyword,
        reasoning=result.reasoning,
    )


# ── BUDGETS ───────────────────────────────────────────────────────────────────

@router.post(
    "/budgets/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set a monthly budget for a category",
)
def set_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Set or update a monthly spending limit for a category.
    Example: limit food_groceries to Rs. 15,000 in May 2025.
    """
    budget = ExpenseService.set_budget(db, current_user, data)
    return BudgetResponse.model_validate(budget)


@router.get(
    "/budgets/",
    response_model=list[BudgetResponse],
    summary="Get all budgets with current spending progress",
)
def get_budgets(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns all budgets for a month, enriched with:
    - How much you've spent so far
    - How much remains
    - Percentage of budget used

    This powers the budget progress bars in the dashboard.
    """
    enriched = ExpenseService.get_budgets_with_spending(db, current_user, month, year)
    result = []
    for item in enriched:
        b = BudgetResponse.model_validate(item["budget"])
        b.spent_so_far = item["spent_so_far"]
        b.remaining = item["remaining"]
        b.usage_percent = item["usage_percent"]
        result.append(b)
    return result
