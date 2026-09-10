from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from datetime import timedelta
from pydantic import BaseModel
from app.database import get_db
from app import models, schemas
from app.ai.simulations import FinancialSimulator
from app.deps import get_current_user
from collections import defaultdict

router = APIRouter()
simulator = FinancialSimulator()


class ReductionPercentages(BaseModel):
    reduction_percentages: Dict[str, float] = {}


def _monthly_rates(transactions):
    dated = [t for t in transactions if t.date]
    if not dated:
        return 0.0, {}
    latest = max(t.date for t in dated)
    if latest.tzinfo:
        latest = latest.replace(tzinfo=None)
    start = latest - timedelta(days=365)
    window = []
    for t in dated:
        dt = t.date.replace(tzinfo=None) if t.date.tzinfo else t.date
        if dt >= start and dt.year >= latest.year - 3:
            window.append(t)
    if not window:
        window = dated
    first = min((t.date.replace(tzinfo=None) if t.date.tzinfo else t.date) for t in window)
    last = max((t.date.replace(tzinfo=None) if t.date.tzinfo else t.date) for t in window)
    span_days = max(30, (last - first).days + 1)
    scale = 30.0 / span_days
    income = sum(abs(t.amount) for t in window if t.transaction_type == "income")
    spending = defaultdict(float)
    expenses = 0.0
    for t in window:
        if t.transaction_type == "expense":
            expenses += abs(t.amount)
            if t.category:
                spending[t.category] += abs(t.amount)
    monthly_surplus = (income - expenses) * scale
    monthly_spending = {cat: total * scale for cat, total in spending.items()}
    return monthly_surplus, monthly_spending


@router.post("/goal-scenario", response_model=Dict)
async def simulate_goal_scenario(
    goal_id: int = Query(...),
    request_body: ReductionPercentages = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    reduction_percentages = request_body.reduction_percentages
    if not isinstance(reduction_percentages, dict):
        raise HTTPException(status_code=400, detail="reduction_percentages must be a dictionary")

    for key, value in reduction_percentages.items():
        try:
            reduction_percentages[key] = float(value)
            if reduction_percentages[key] < 0 or reduction_percentages[key] > 100:
                raise HTTPException(
                    status_code=400,
                    detail=f"Reduction percentage for '{key}' must be between 0 and 100",
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reduction percentage for '{key}': must be a number",
            )

    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id,
    ).all()
    monthly_surplus, monthly_spending = _monthly_rates(transactions)

    return simulator.simulate_goal_scenario(
        current_savings=goal.current_amount,
        monthly_contribution=monthly_surplus,
        target_amount=goal.target_amount,
        current_monthly_spending=monthly_spending,
        reduction_percentages=reduction_percentages,
    )


@router.post("/monte-carlo", response_model=schemas.MonteCarloResult)
async def monte_carlo_simulation(
    payload: schemas.MonteCarloRequest,
    current_user: models.User = Depends(get_current_user),
):
    result = simulator.monte_carlo_investment(
        initial_investment=payload.initial_investment,
        monthly_contribution=payload.monthly_contribution,
        years=payload.years,
        expected_return=payload.expected_return,
        volatility=payload.volatility,
        simulations=payload.simulations,
    )
    return schemas.MonteCarloResult(**result)


@router.post("/opportunity-cost", response_model=schemas.OpportunityCost)
async def calculate_opportunity_cost(
    spending_amount: float,
    time_horizon_years: float = 1.0,
    expected_return: float = 0.07,
    current_user: models.User = Depends(get_current_user),
):
    result = simulator.calculate_opportunity_cost(
        spending_amount=spending_amount,
        time_horizon_years=time_horizon_years,
        expected_return=expected_return,
    )
    return schemas.OpportunityCost(**result)
