from sqlalchemy import Column, Integer, String, Numeric, Boolean,DateTime, Date, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class ExpenseCategory(str, enum.Enum):
    food_groceries = "food_groceries"
    street_food = "street_food"
    restaurants = "restaurants"
    transport_bus = "transport_bus"
    transport_tuk = "transport_tuk"
    transport_fuel = "transport_fuel"
    transport_rideshare = "transport_rideshare"
    electricity_ceb = "electricity_ceb"
    water_nwsdb = "water_nwsdb"
    mobile_dialog = "mobile_dialog"
    mobile_mobitel = "mobile_mobitel"
    internet = "internet"
    rent = "rent"
    healthcare = "healthcare"
    education = "education"
    clothing = "clothing"
    entertainment = "entertainment"
    pola_market = "pola_market"
    supermarket = "supermarket"
    salary = "salary"
    freelance = "freelance"
    business_income = "business_income"
    other_income = "other_income"
    other_expense = "other_expense"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)           
    description = Column(String(500), nullable=False)
    category = Column(SAEnum(ExpenseCategory), nullable=False)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)
    transaction_date = Column(Date, nullable=False)


    auto_categorized = Column(Boolean, default=False)         
    categorization_confidence = Column(Numeric(3, 2), default=1.0)  
    raw_description = Column(String(500), nullable=True)      

    notes = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="expenses")

    def __repr__(self):
        return f"<Expense id={self.id} amount={self.amount} category={self.category}>"


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    category = Column(SAEnum(ExpenseCategory), nullable=False)
    monthly_limit = Column(Numeric(12, 2), nullable=False)    
    month = Column(Integer, nullable=False)                  
    year = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="budgets")
