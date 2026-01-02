"""
API endpoints for probabilistic cash-flow risk analysis.
"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.ai.cashflow_risk import CashFlowRiskAnalyzer

router = APIRouter()
risk_analyzer = CashFlowRiskAnalyzer()

@router.get("/cashflow-risk", response_model=schemas.CashFlowRiskAnalysis)
async def get_cashflow_risk(
    horizon_days: int = Query(30, description="Risk analysis horizon in days"),
    db: Session = Depends(get_db)
):
    """
    Compute probabilistic cash-flow risk analysis.
    
    Returns:
    - Failure probability: P(cash flow < 0)
    - Expected shortfall: Tail risk when failure occurs
    - Risk attribution: Which categories drive risk
    - Goal-conditioned risks: Probability of missing goals
    """
    user_id = 1  # TODO: Auth
    
    # Get recent transactions (last 90 days for distribution estimation)
    start_date = datetime.now() - timedelta(days=90)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= start_date
    ).all()
    
    # Get goals
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).all()
    
    # Convert to dict format
    transaction_dicts = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "transaction_type": t.transaction_type,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    goals_dicts = [
        {
            "id": g.id,
            "name": g.name,
            "current_amount": g.current_amount,
            "target_amount": g.target_amount,
            "target_date": g.target_date.isoformat() if g.target_date else None
        }
        for g in goals
    ]
    
    # Run risk analysis
    risk_result = risk_analyzer.analyze_risk(
        transaction_dicts,
        goals_dicts,
        horizon_days
    )
    
    # Convert to response format
    return schemas.CashFlowRiskAnalysis(
        failure_probability=risk_result["failure_probability"],
        expected_shortfall=risk_result["expected_shortfall"],
        mean_cashflow=risk_result["mean_cashflow"],
        std_cashflow=risk_result["std_cashflow"],
        risk_drivers=[
            schemas.RiskDriver(**driver) for driver in risk_result["risk_drivers"]
        ],
        goal_risks=[
            schemas.GoalRisk(**risk) for risk in risk_result["goal_risks"]
        ],
        runway_days=risk_result["runway_days"],
        income_stats=risk_result["income_stats"],
        expense_stats=risk_result["expense_stats"]
    )

@router.post("/stress-test", response_model=schemas.StressTestResult)
async def stress_test_cashflow(
    scenarios: Dict[str, float] = Body(..., description="Shock scenarios, e.g., {'rent': 1.1, 'income': 0.9}"),
    horizon_days: int = Query(30, description="Risk analysis horizon in days"),
    db: Session = Depends(get_db)
):
    """
    Stress test: Apply shocks and recompute risk.
    
    Example scenarios:
    {
        "rent": 1.1,      # 10% increase
        "income": 0.9,    # 10% decrease
        "dining": 0.8     # 20% decrease
    }
    """
    user_id = 1  # TODO: Auth
    
    # Get recent transactions
    start_date = datetime.now() - timedelta(days=90)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= start_date
    ).all()
    
    # Get goals
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).all()
    
    # Convert to dict format
    transaction_dicts = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "transaction_type": t.transaction_type,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    goals_dicts = [
        {
            "id": g.id,
            "name": g.name,
            "current_amount": g.current_amount,
            "target_amount": g.target_amount,
            "target_date": g.target_date.isoformat() if g.target_date else None
        }
        for g in goals
    ]
    
    # Run stress test
    stress_result = risk_analyzer.stress_test(
        transaction_dicts,
        scenarios,
        goals_dicts
    )
    
    # Convert to response format
    return schemas.StressTestResult(
        base_risk=schemas.CashFlowRiskAnalysis(
            failure_probability=stress_result["base_risk"]["failure_probability"],
            expected_shortfall=stress_result["base_risk"]["expected_shortfall"],
            mean_cashflow=stress_result["base_risk"]["mean_cashflow"],
            std_cashflow=stress_result["base_risk"]["std_cashflow"],
            risk_drivers=[
                schemas.RiskDriver(**driver) for driver in stress_result["base_risk"]["risk_drivers"]
            ],
            goal_risks=[
                schemas.GoalRisk(**risk) for risk in stress_result["base_risk"]["goal_risks"]
            ],
            runway_days=stress_result["base_risk"]["runway_days"],
            income_stats=stress_result["base_risk"]["income_stats"],
            expense_stats=stress_result["base_risk"]["expense_stats"]
        ),
        shocked_risk=schemas.CashFlowRiskAnalysis(
            failure_probability=stress_result["shocked_risk"]["failure_probability"],
            expected_shortfall=stress_result["shocked_risk"]["expected_shortfall"],
            mean_cashflow=stress_result["shocked_risk"]["mean_cashflow"],
            std_cashflow=stress_result["shocked_risk"]["std_cashflow"],
            risk_drivers=[
                schemas.RiskDriver(**driver) for driver in stress_result["shocked_risk"]["risk_drivers"]
            ],
            goal_risks=[
                schemas.GoalRisk(**risk) for risk in stress_result["shocked_risk"]["goal_risks"]
            ],
            runway_days=stress_result["shocked_risk"]["runway_days"],
            income_stats=stress_result["shocked_risk"]["income_stats"],
            expense_stats=stress_result["shocked_risk"]["expense_stats"]
        ),
        delta=stress_result["delta"],
        scenarios=stress_result["scenarios"]
    )

