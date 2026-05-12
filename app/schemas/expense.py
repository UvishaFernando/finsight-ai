from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from app.models.expense import ExpenseCategory, TransactionType

class ExpenseCreate(BaseModel):
    amount: Decimal
    description: str
    transaction_date: date
    category: Optional[ExpenseCategory] = None
    transaction_type: Optional[TransactionType] = None
    notes: Optional[str] = None
    is_recurring: bool = False

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) :
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > Decimal("10000000"):
            raise ValueError("Amount exceeds maximum allowed (10,000,000)")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) :
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty")
        return v


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    category: Optional[ExpenseCategory] = None
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[date] = None
    notes: Optional[str] = None
    is_recurring: Optional[bool] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[Decimal]) :
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class ExpenseResponse(BaseModel):
    id: int
    amount: Decimal
    description: str
    category: ExpenseCategory
    transaction_type: TransactionType
    transaction_date: date
    auto_categorized: bool
    categorization_confidence: Optional[Decimal]
    notes: Optional[str]
    is_recurring: bool
    created_at: datetime

    categorization_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BudgetCreate(BaseModel):
    category: ExpenseCategory
    monthly_limit: Decimal
    month: int
    year: int

    @field_validator("monthly_limit")
    @classmethod
    def limit_positive(cls, v: Decimal) :
        if v <= 0:
            raise ValueError("Budget limit must be greater than 0")
        return v

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) :
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) :
        if not 2020 <= v <= 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return v


class BudgetResponse(BaseModel):
    id: int
    category: ExpenseCategory
    monthly_limit: Decimal
    month: int
    year: int
    spent_so_far: Optional[Decimal] = None      
    remaining: Optional[Decimal] = None          
    usage_percent: Optional[float] = None        

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    category: ExpenseCategory
    total: Decimal
    count: int
    percentage: float                           


class MonthlySummary(BaseModel):
    month: int
    year: int
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    savings_rate: float                          
    transaction_count: int
    category_breakdown: List[CategoryBreakdown]


class WasteAlert(BaseModel):
    category: ExpenseCategory
    this_month: Decimal
    avg_previous_months: Decimal
    overspend_percent: float
    overspend_amount: Decimal
    severity: str                               
    message: str
    tip: str


class WasteReport(BaseModel):
    analysis_period_days: int
    alerts: List[WasteAlert]
    total_potential_savings: Decimal
    summary: str


class CategorizationPreview(BaseModel):
    description: str
    suggested_category: ExpenseCategory
    suggested_type: TransactionType
    confidence: float
    matched_keyword: str
    reasoning: str
