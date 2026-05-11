from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Text
from sqlalchemy.sql import func
from app.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)           
    item_key = Column(String(50), index=True, nullable=False) 
    category = Column(String(50), nullable=False)            
    price_lkr = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(30), nullable=False)                 
    source = Column(String(100), nullable=True)               
    price_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    alert_type = Column(String(50), nullable=False)   
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")     
    is_read = Column(String(5), default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
