from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    transactions = relationship("Transaction", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, index=True)
    subcategory = Column(String)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    transaction_type = Column(String)  # 'income' or 'expense'
    merchant = Column(String)
    ai_categorized = Column(Boolean, default=False)
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="transactions")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime(timezone=True))
    goal_type = Column(String)  # 'savings', 'debt_payoff', 'investment', 'purchase'
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="goals")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alert_type = Column(String)  # 'unusual_spending', 'cash_shortage', 'goal_milestone', 'recommendation'
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String)  # 'info', 'warning', 'critical'
    read = Column(Boolean, default=False)
    alert_metadata = Column(JSON)  # Additional data for the alert (renamed from 'metadata' - reserved word)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="alerts")

class SpendingPattern(Base):
    __tablename__ = "spending_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String, nullable=False)
    average_amount = Column(Float)
    frequency = Column(String)  # 'daily', 'weekly', 'monthly'
    trend = Column(String)  # 'increasing', 'decreasing', 'stable'
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Simulation(Base):
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    simulation_type = Column(String)  # 'goal_scenario', 'monte_carlo', 'opportunity_cost'
    parameters = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

