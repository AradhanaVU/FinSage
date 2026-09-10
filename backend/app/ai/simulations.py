from typing import Dict
import math
import random
import statistics


def _ceil_months(remaining: float, monthly: float) -> int:
    if monthly <= 0:
        return 999
    if remaining <= 0:
        return 0
    return int(math.ceil(remaining / monthly))


def interpolated_percentile(sorted_values, p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = p * (len(sorted_values) - 1)
    lo = int(math.floor(rank))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return float(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac)


class FinancialSimulator:
    def simulate_goal_scenario(
        self,
        current_savings: float,
        monthly_contribution: float,
        target_amount: float,
        current_monthly_spending: Dict[str, float],
        reduction_percentages: Dict[str, float],
    ) -> Dict:
        baseline_months = _ceil_months(target_amount - current_savings, monthly_contribution)
        total_reduction = sum(
            current_monthly_spending.get(cat, 0.0) * (float(percent) / 100.0)
            for cat, percent in reduction_percentages.items()
        )
        optimized_contribution = monthly_contribution + total_reduction
        optimized_months = _ceil_months(target_amount - current_savings, optimized_contribution)
        months_saved = max(0, baseline_months - optimized_months) if baseline_months < 999 else 0

        scenarios = [
            {
                "scenario_name": "Current Plan",
                "monthly_contribution": monthly_contribution,
                "months_to_goal": baseline_months,
                "total_contributed": monthly_contribution * baseline_months if baseline_months < 999 else None,
                "savings_from_reductions": 0,
            },
            {
                "scenario_name": "With Spending Reductions",
                "monthly_contribution": optimized_contribution,
                "months_to_goal": optimized_months,
                "total_contributed": optimized_contribution * optimized_months if optimized_months < 999 else None,
                "savings_from_reductions": total_reduction,
                "months_saved": months_saved,
            },
        ]
        return {
            "scenarios": scenarios,
            "best_scenario": scenarios[-1],
            "time_saved_days": months_saved * 30,
            "observed_monthly_surplus": monthly_contribution,
            "observed_monthly_spending": current_monthly_spending,
        }

    def monte_carlo_investment(
        self,
        initial_investment: float,
        monthly_contribution: float,
        years: int,
        expected_return: float = 0.07,
        volatility: float = 0.15,
        simulations: int = 1000,
    ) -> Dict:
        years = max(1, min(int(years), 50))
        simulations = max(100, min(int(simulations), 10000))
        monthly_rate = (1.0 + expected_return) ** (1.0 / 12.0) - 1.0
        monthly_vol = volatility / math.sqrt(12.0)
        months = years * 12
        cash_path = initial_investment + monthly_contribution * months

        results = []
        for _ in range(simulations):
            balance = initial_investment
            for _month in range(months):
                balance += monthly_contribution
                shock = random.gauss(monthly_rate, monthly_vol)
                balance *= (1.0 + shock)
            results.append(balance)
        results.sort()

        return {
            "simulations": simulations,
            "mean_outcome": statistics.mean(results),
            "median_outcome": statistics.median(results),
            "percentile_5": interpolated_percentile(results, 0.05),
            "percentile_25": interpolated_percentile(results, 0.25),
            "percentile_75": interpolated_percentile(results, 0.75),
            "percentile_95": interpolated_percentile(results, 0.95),
            "success_probability": sum(1 for r in results if r > cash_path) / simulations,
            "cash_path_value": cash_path,
        }

    def calculate_opportunity_cost(
        self,
        spending_amount: float,
        time_horizon_years: float = 1.0,
        expected_return: float = 0.07,
    ) -> Dict:
        future_value = spending_amount * ((1 + expected_return) ** time_horizon_years)
        opportunity_cost = future_value - spending_amount
        if opportunity_cost > spending_amount * 0.1:
            recommendation = (
                f"Investing ${spending_amount:.2f} at {expected_return:.1%} annual compounding "
                f"could grow to ${future_value:.2f} in {time_horizon_years:g} years "
                f"(${opportunity_cost:.2f} given up)."
            )
        else:
            recommendation = (
                f"At {expected_return:.1%} annual compounding, ${spending_amount:.2f} could grow "
                f"to ${future_value:.2f} over {time_horizon_years:g} years."
            )
        return {
            "spending_amount": spending_amount,
            "potential_investment_return": future_value,
            "time_horizon_years": time_horizon_years,
            "opportunity_cost": opportunity_cost,
            "recommendation": recommendation,
        }
