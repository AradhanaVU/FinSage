"""API endpoints for probabilistic cash-flow risk analysis."""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Dict
from app.database import get_db
from app import models, schemas
from app.ai.cashflow_risk import CashFlowRiskAnalyzer
from app.deps import get_current_user

router = APIRouter()
risk_analyzer = CashFlowRiskAnalyzer()


def _to_analysis(risk_result: dict) -> schemas.CashFlowRiskAnalysis:
    return schemas.CashFlowRiskAnalysis(
        failure_probability=risk_result["failure_probability"],
        expected_shortfall=risk_result["expected_shortfall"],
        mean_cashflow=risk_result["mean_cashflow"],
        std_cashflow=risk_result["std_cashflow"],
        risk_drivers=[schemas.RiskDriver(**driver) for driver in risk_result["risk_drivers"]],
        goal_risks=[schemas.GoalRisk(**risk) for risk in risk_result["goal_risks"]],
        runway_days=risk_result["runway_days"],
        income_stats=risk_result["income_stats"],
        expense_stats=risk_result["expense_stats"],
    )


def _user_payloads(db: Session, user_id: int):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
    ).all()
    goals = db.query(models.Goal).filter(models.Goal.user_id == user_id).all()
    transaction_dicts = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "transaction_type": t.transaction_type,
            "date": t.date.isoformat() if t.date else None,
        }
        for t in transactions
    ]
    goals_dicts = [
        {
            "id": g.id,
            "name": g.name,
            "current_amount": g.current_amount,
            "target_amount": g.target_amount,
            "target_date": g.target_date.isoformat() if g.target_date else None,
        }
        for g in goals
    ]
    return transaction_dicts, goals_dicts


@router.get("/cashflow-risk", response_model=schemas.CashFlowRiskAnalysis)
async def get_cashflow_risk(
    horizon_days: int = Query(30, description="Risk analysis horizon in days"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transaction_dicts, goals_dicts = _user_payloads(db, current_user.id)
    risk_result = risk_analyzer.analyze_risk(transaction_dicts, goals_dicts, horizon_days)
    return _to_analysis(risk_result)


@router.post("/stress-test", response_model=schemas.StressTestResult)
async def stress_test_cashflow(
    scenarios: Dict[str, float] = Body(..., description="Shock scenarios"),
    horizon_days: int = Query(30, description="Risk analysis horizon in days"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transaction_dicts, goals_dicts = _user_payloads(db, current_user.id)
    stress_result = risk_analyzer.stress_test(
        transaction_dicts,
        scenarios,
        goals_dicts,
        horizon_days,
    )
    return schemas.StressTestResult(
        base_risk=_to_analysis(stress_result["base_risk"]),
        shocked_risk=_to_analysis(stress_result["shocked_risk"]),
        delta=stress_result["delta"],
        scenarios=stress_result["scenarios"],
    )
