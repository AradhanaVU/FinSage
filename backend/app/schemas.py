from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    description: str
    date: datetime
    transaction_type: str
    merchant: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    category: Optional[str] = None
    subcategory: Optional[str] = None
    ai_categorized: bool = False
    confidence_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Goal schemas
class GoalBase(BaseModel):
    name: str
    target_amount: float
    target_date: Optional[datetime] = None
    goal_type: str
    priority: int = 1

class GoalCreate(GoalBase):
    pass

class GoalResponse(GoalBase):
    id: int
    user_id: int
    current_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Alert schemas
class AlertResponse(BaseModel):
    id: int
    user_id: int
    alert_type: str
    title: str
    message: str
    severity: str
    read: bool
    alert_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI Insights schemas
class SpendingAnalysis(BaseModel):
    category: str
    total_amount: float
    transaction_count: int
    average_amount: float
    trend: str
    percentage_of_total: float

class SpendingForecast(BaseModel):
    date: datetime
    predicted_amount: float
    confidence_interval_lower: float
    confidence_interval_upper: float

class AnomalyDetection(BaseModel):
    transaction_id: int
    anomaly_score: float
    reason: str
    severity: str

class PatternDetection(BaseModel):
    category: str
    pattern_type: str
    description: str
    impact: str

# Simulation schemas
class ScenarioSimulation(BaseModel):
    scenario_name: str
    parameters: Dict[str, Any]
    projected_outcome: Dict[str, Any]
    time_to_goal: Optional[int] = None  # days
    savings_impact: float

class MonteCarloResult(BaseModel):
    simulations: int
    mean_outcome: float
    median_outcome: float
    percentile_5: float
    percentile_95: float
    success_probability: float

class OpportunityCost(BaseModel):
    spending_amount: float
    potential_investment_return: float
    time_horizon_years: float
    opportunity_cost: float
    recommendation: str

# Chat schemas
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

# Cash Flow Risk Analysis schemas
class RiskDriver(BaseModel):
    category: str
    risk_share: float  # Percentage of total risk (0-1)
    variance: float
    std: float
    mean: float
    cv: float  # Coefficient of variation
    contribution: float  # Percentage contribution

class GoalRisk(BaseModel):
    goal_id: int
    goal_name: str
    failure_probability: float  # P(goal not reached)
    expected_shortfall: float
    months_to_goal: float
    remaining_amount: float

class CashFlowRiskAnalysis(BaseModel):
    failure_probability: float  # P(C < 0)
    expected_shortfall: float  # E[C | C < 0]
    mean_cashflow: float  # μ_C
    std_cashflow: float  # σ_C
    risk_drivers: List[RiskDriver]
    goal_risks: List[GoalRisk]
    runway_days: float  # Days until expected failure
    income_stats: Dict[str, float]
    expense_stats: Dict[str, Any]

class StressTestResult(BaseModel):
    base_risk: CashFlowRiskAnalysis
    shocked_risk: CashFlowRiskAnalysis
    delta: Dict[str, float]
    scenarios: Dict[str, float]

