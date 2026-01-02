from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import random
import statistics

class FinancialSimulator:
    def __init__(self):
        pass
    
    def simulate_goal_scenario(
        self,
        current_savings: float,
        monthly_contribution: float,
        target_amount: float,
        current_monthly_spending: Dict[str, float],
        reduction_percentages: Dict[str, float]
    ) -> Dict:
        """
        Simulate different scenarios for reaching a financial goal.
        """
        scenarios = []
        
        # Baseline scenario
        baseline_months = self._calculate_months_to_goal(
            current_savings, monthly_contribution, target_amount
        )
        scenarios.append({
            "scenario_name": "Current Plan",
            "monthly_contribution": monthly_contribution,
            "months_to_goal": baseline_months,
            "total_contributed": monthly_contribution * baseline_months,
            "savings_from_reductions": 0
        })
        
        # Calculate savings from spending reductions
        total_reduction = sum(
            current_monthly_spending.get(cat, 0) * (percent / 100)
            for cat, percent in reduction_percentages.items()
        )
        
        # Optimized scenario
        new_monthly_contribution = monthly_contribution + total_reduction
        optimized_months = self._calculate_months_to_goal(
            current_savings, new_monthly_contribution, target_amount
        )
        
        scenarios.append({
            "scenario_name": "With Spending Reductions",
            "monthly_contribution": new_monthly_contribution,
            "months_to_goal": optimized_months,
            "total_contributed": new_monthly_contribution * optimized_months,
            "savings_from_reductions": total_reduction,
            "months_saved": baseline_months - optimized_months if baseline_months > 0 else 0
        })
        
        return {
            "scenarios": scenarios,
            "best_scenario": scenarios[-1],
            "time_saved_days": (baseline_months - optimized_months) * 30 if baseline_months > optimized_months else 0
        }
    
    def _calculate_months_to_goal(
        self,
        current: float,
        monthly: float,
        target: float
    ) -> int:
        """Calculate months needed to reach goal."""
        if monthly <= 0:
            return 999  # Never reachable
        
        remaining = target - current
        if remaining <= 0:
            return 0
        
        months = remaining / monthly
        return int(months) + (1 if months % 1 > 0 else 0)
    
    def monte_carlo_investment(
        self,
        initial_investment: float,
        monthly_contribution: float,
        years: int,
        expected_return: float = 0.07,
        volatility: float = 0.15,
        simulations: int = 1000
    ) -> Dict:
        """
        Run Monte Carlo simulation for investment planning.
        """
        results = []
        
        for _ in range(simulations):
            balance = initial_investment
            monthly_return = expected_return / 12
            
            for month in range(years * 12):
                # Add monthly contribution
                balance += monthly_contribution
                
                # Apply random return based on volatility
                random_return = random.gauss(monthly_return, volatility / (12 ** 0.5))
                balance *= (1 + random_return)
            
            results.append(balance)
        
        results.sort()
        
        return {
            "simulations": simulations,
            "mean_outcome": statistics.mean(results),
            "median_outcome": statistics.median(results),
            "percentile_5": results[int(simulations * 0.05)],
            "percentile_95": results[int(simulations * 0.95)],
            "percentile_25": results[int(simulations * 0.25)],
            "percentile_75": results[int(simulations * 0.75)],
            "success_probability": sum(1 for r in results if r > initial_investment * 2) / simulations
        }
    
    def calculate_opportunity_cost(
        self,
        spending_amount: float,
        time_horizon_years: float = 1.0,
        expected_return: float = 0.07
    ) -> Dict:
        """
        Calculate opportunity cost of spending vs investing.
        """
        # Future value if invested
        future_value = spending_amount * ((1 + expected_return) ** time_horizon_years)
        opportunity_cost = future_value - spending_amount
        
        # Generate recommendation
        if opportunity_cost > spending_amount * 0.1:  # More than 10% opportunity cost
            recommendation = f"Consider investing ${spending_amount:.2f} instead. Over {time_horizon_years} years, you could have ${future_value:.2f} (potential gain: ${opportunity_cost:.2f})."
        else:
            recommendation = f"This spending has a moderate opportunity cost. If invested, ${spending_amount:.2f} could grow to ${future_value:.2f} over {time_horizon_years} years."
        
        return {
            "spending_amount": spending_amount,
            "potential_investment_return": future_value,
            "time_horizon_years": time_horizon_years,
            "opportunity_cost": opportunity_cost,
            "recommendation": recommendation
        }


