from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app import models, schemas
from app.ai.simulations import FinancialSimulator
from collections import defaultdict

router = APIRouter()
simulator = FinancialSimulator()

class ReductionPercentages(BaseModel):
    reduction_percentages: Dict[str, float] = {}

@router.post("/goal-scenario", response_model=Dict)
async def simulate_goal_scenario(
    goal_id: int = Query(...),
    request_body: ReductionPercentages = Body(...),
    db: Session = Depends(get_db)
):
    """Simulate different scenarios for reaching a goal."""
    from fastapi import HTTPException
    
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == 1  # TODO: Auth
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Validate reduction_percentages
    reduction_percentages = request_body.reduction_percentages
    if not isinstance(reduction_percentages, dict):
        raise HTTPException(status_code=400, detail="reduction_percentages must be a dictionary")
    
    # Ensure all values are valid numbers
    for key, value in reduction_percentages.items():
        try:
            reduction_percentages[key] = float(value)
            if reduction_percentages[key] < 0 or reduction_percentages[key] > 100:
                raise HTTPException(status_code=400, detail=f"Reduction percentage for '{key}' must be between 0 and 100")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid reduction percentage for '{key}': must be a number")
    
    # Get recent spending by category
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.transaction_type == "expense",
        models.Transaction.date >= datetime.now() - timedelta(days=30)
    ).all()
    
    category_spending = defaultdict(float)
    for txn in transactions:
        if txn.category:
            category_spending[txn.category] += abs(txn.amount)
    
    # Calculate current monthly contribution (simplified)
    monthly_contribution = 500.0  # Default, could be calculated from income - expenses
    
    result = simulator.simulate_goal_scenario(
        current_savings=goal.current_amount,
        monthly_contribution=monthly_contribution,
        target_amount=goal.target_amount,
        current_monthly_spending=dict(category_spending),
        reduction_percentages=reduction_percentages
    )
    
    return result

@router.post("/monte-carlo", response_model=schemas.MonteCarloResult)
async def monte_carlo_simulation(
    initial_investment: float,
    monthly_contribution: float,
    years: int,
    expected_return: float = 0.07,
    volatility: float = 0.15,
    simulations: int = 1000
):
    """Run Monte Carlo simulation for investment planning."""
    result = simulator.monte_carlo_investment(
        initial_investment=initial_investment,
        monthly_contribution=monthly_contribution,
        years=years,
        expected_return=expected_return,
        volatility=volatility,
        simulations=simulations
    )
    
    return schemas.MonteCarloResult(**result)

@router.post("/opportunity-cost", response_model=schemas.OpportunityCost)
async def calculate_opportunity_cost(
    spending_amount: float,
    time_horizon_years: float = 1.0,
    expected_return: float = 0.07
):
    """Calculate opportunity cost of spending vs investing."""
    result = simulator.calculate_opportunity_cost(
        spending_amount=spending_amount,
        time_horizon_years=time_horizon_years,
        expected_return=expected_return
    )
    
    return schemas.OpportunityCost(**result)

