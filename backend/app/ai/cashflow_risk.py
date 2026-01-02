"""
Probabilistic Cash-Flow Risk Analysis Engine

This module models cash flow as a random variable and computes:
- Probability of cash-flow failure (negative cash flow)
- Expected shortfall (tail risk)
- Risk attribution by category
- Goal-conditioned risk probabilities
- Stress testing scenarios
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math

# Optional numpy for more advanced calculations
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class CashFlowRiskAnalyzer:
    """
    Analyzes probabilistic cash-flow risk from transaction data.
    
    Core math:
    - Monthly net cash flow: C_t = I_t - E_t (random variable)
    - Income: I_t ~ N(μ_I, σ_I²)
    - Expenses: E_t = Σ E_k,t where E_k,t ~ N(μ_k, σ_k²)
    - Net cash flow: C_t ~ N(μ_C, σ_C²) where:
        μ_C = μ_I - Σ μ_k
        σ_C² = σ_I² + Σ σ_k²
    - Failure probability: P(C_t < 0) = Φ(-μ_C / σ_C)
    """
    
    def __init__(self):
        pass
    
    def analyze_risk(
        self,
        transactions: List[Dict],
        goals: Optional[List[Dict]] = None,
        horizon_days: int = 30
    ) -> Dict:
        """
        Main risk analysis function.
        
        Returns:
        {
            "failure_probability": float,  # P(C < 0)
            "expected_shortfall": float,   # E[C | C < 0]
            "mean_cashflow": float,        # μ_C
            "std_cashflow": float,         # σ_C
            "risk_drivers": List[Dict],    # Attribution by category
            "goal_risks": List[Dict],      # Goal-conditioned risks
            "runway_days": float           # Days until failure (expected)
        }
        """
        if not transactions:
            return self._empty_risk_result()
        
        # Extract income and expense distributions
        income_stats = self._compute_income_distribution(transactions)
        expense_stats = self._compute_expense_distributions(transactions)
        
        # Compute net cash flow distribution
        mean_cashflow = income_stats["mean"] - expense_stats["total_mean"]
        var_cashflow = income_stats["variance"] + expense_stats["total_variance"]
        std_cashflow = math.sqrt(var_cashflow) if var_cashflow > 0 else 0.0
        
        # Probability of failure (negative cash flow)
        failure_prob = self._compute_failure_probability(mean_cashflow, std_cashflow)
        
        # Expected shortfall (tail risk)
        expected_shortfall = self._compute_expected_shortfall(mean_cashflow, std_cashflow)
        
        # Risk attribution by category
        risk_drivers = self._compute_risk_attribution(
            expense_stats["category_stats"],
            var_cashflow
        )
        
        # Goal-conditioned risks
        goal_risks = []
        if goals:
            goal_risks = self._compute_goal_risks(
                goals,
                mean_cashflow,
                std_cashflow,
                horizon_days
            )
        
        # Runway calculation (days until expected failure)
        runway_days = self._compute_runway(mean_cashflow, std_cashflow)
        
        return {
            "failure_probability": failure_prob,
            "expected_shortfall": expected_shortfall,
            "mean_cashflow": mean_cashflow,
            "std_cashflow": std_cashflow,
            "risk_drivers": risk_drivers,
            "goal_risks": goal_risks,
            "runway_days": runway_days,
            "income_stats": income_stats,
            "expense_stats": expense_stats
        }
    
    def _compute_income_distribution(self, transactions: List[Dict]) -> Dict:
        """Compute income distribution: I_t ~ N(μ_I, σ_I²)"""
        income_transactions = [
            t for t in transactions
            if t.get("transaction_type") == "income"
        ]
        
        if not income_transactions:
            return {"mean": 0.0, "variance": 0.0, "std": 0.0}
        
        amounts = [abs(t["amount"]) for t in income_transactions]
        mean = statistics.mean(amounts)
        
        if len(amounts) > 1:
            variance = statistics.variance(amounts)
            std = statistics.stdev(amounts)
        else:
            # If only one income, assume some variance (10% of mean)
            variance = (mean * 0.1) ** 2
            std = mean * 0.1
        
        return {
            "mean": mean,
            "variance": variance,
            "std": std,
            "count": len(amounts)
        }
    
    def _compute_expense_distributions(self, transactions: List[Dict]) -> Dict:
        """
        Compute expense distributions by category: E_k,t ~ N(μ_k, σ_k²)
        
        Total expense variance: σ_E² = Σ σ_k²
        """
        expense_transactions = [
            t for t in transactions
            if t.get("transaction_type") == "expense"
        ]
        
        if not expense_transactions:
            return {
                "total_mean": 0.0,
                "total_variance": 0.0,
                "category_stats": {}
            }
        
        # Group by category
        category_data = defaultdict(list)
        for txn in expense_transactions:
            category = txn.get("category") or "Uncategorized"
            category_data[category].append(abs(txn["amount"]))
        
        category_stats = {}
        total_mean = 0.0
        total_variance = 0.0
        
        for category, amounts in category_data.items():
            if len(amounts) == 0:
                continue
            
            mean = statistics.mean(amounts)
            total_mean += mean
            
            if len(amounts) > 1:
                variance = statistics.variance(amounts)
                std = statistics.stdev(amounts)
            else:
                # Single transaction: assume 20% variance
                variance = (mean * 0.2) ** 2
                std = mean * 0.2
            
            total_variance += variance
            
            # Coefficient of variation (normalized risk)
            cv = std / mean if mean > 0 else 0.0
            
            category_stats[category] = {
                "mean": mean,
                "variance": variance,
                "std": std,
                "cv": cv,  # Coefficient of variation
                "count": len(amounts)
            }
        
        return {
            "total_mean": total_mean,
            "total_variance": total_variance,
            "total_std": math.sqrt(total_variance) if total_variance > 0 else 0.0,
            "category_stats": category_stats
        }
    
    def _compute_failure_probability(
        self,
        mean_cashflow: float,
        std_cashflow: float
    ) -> float:
        """
        Compute P(C < 0) = Φ(-μ_C / σ_C)
        
        Where Φ is the standard normal CDF.
        """
        if std_cashflow == 0:
            return 1.0 if mean_cashflow < 0 else 0.0
        
        z_score = -mean_cashflow / std_cashflow
        
        # Standard normal CDF approximation
        # Using error function: Φ(z) = 0.5 * (1 + erf(z / √2))
        if HAS_NUMPY:
            prob = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
        else:
            # Simple approximation for standard normal CDF
            prob = self._normal_cdf(z_score)
        
        return max(0.0, min(1.0, prob))
    
    def _normal_cdf(self, z: float) -> float:
        """Approximate standard normal CDF using error function approximation."""
        # Abramowitz and Stegun approximation
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        d = 0.3989423 * math.exp(-z * z / 2)
        p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
        
        if z > 0:
            return 1.0 - p
        else:
            return p
    
    def _compute_expected_shortfall(
        self,
        mean_cashflow: float,
        std_cashflow: float
    ) -> float:
        """
        Compute expected shortfall: E[C | C < 0]
        
        For normal distribution:
        ES = μ_C - σ_C * φ(z) / Φ(z)
        where z = -μ_C / σ_C
        """
        if std_cashflow == 0:
            return abs(mean_cashflow) if mean_cashflow < 0 else 0.0
        
        z = -mean_cashflow / std_cashflow
        
        # Standard normal PDF: φ(z)
        phi_z = (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z * z)
        
        # Standard normal CDF: Φ(z)
        phi_cdf = self._normal_cdf(z)
        
        if phi_cdf == 0:
            return 0.0
        
        # Expected shortfall
        es = mean_cashflow - std_cashflow * (phi_z / phi_cdf)
        
        return abs(es) if es < 0 else 0.0
    
    def _compute_risk_attribution(
        self,
        category_stats: Dict[str, Dict],
        total_variance: float
    ) -> List[Dict]:
        """
        Compute risk attribution: Risk Share_k = σ_k² / σ_C²
        
        Returns list sorted by risk contribution (highest first).
        """
        if total_variance == 0:
            return []
        
        attributions = []
        for category, stats in category_stats.items():
            risk_share = stats["variance"] / total_variance if total_variance > 0 else 0.0
            
            attributions.append({
                "category": category,
                "risk_share": risk_share,  # Percentage of total risk
                "variance": stats["variance"],
                "std": stats["std"],
                "mean": stats["mean"],
                "cv": stats["cv"],  # Coefficient of variation
                "contribution": risk_share * 100  # Percentage
            })
        
        # Sort by risk contribution (highest first)
        attributions.sort(key=lambda x: x["risk_share"], reverse=True)
        
        return attributions
    
    def _compute_goal_risks(
        self,
        goals: List[Dict],
        mean_cashflow: float,
        std_cashflow: float,
        horizon_days: int
    ) -> List[Dict]:
        """
        Compute goal-conditioned risk probabilities.
        
        For goal requiring G by time T:
        S_T = Σ C_t ~ N(T * μ_C, T * σ_C²)
        P(goal failure) = P(S_T < G) = Φ((G - T*μ_C) / (√T * σ_C))
        """
        goal_risks = []
        
        for goal in goals:
            current = goal.get("current_amount", 0.0)
            target = goal.get("target_amount", 0.0)
            
            if target <= current:
                # Goal already reached
                goal_risks.append({
                    "goal_id": goal.get("id"),
                    "goal_name": goal.get("name"),
                    "failure_probability": 0.0,
                    "expected_shortfall": 0.0
                })
                continue
            
            remaining = target - current
            
            # Estimate months to goal based on current cash flow
            if mean_cashflow > 0:
                months_to_goal = remaining / mean_cashflow
            else:
                months_to_goal = 999  # Never reachable
            
            # Convert to days
            days_to_goal = months_to_goal * 30
            
            # If goal is beyond horizon, use horizon
            T = min(horizon_days, days_to_goal) / 30.0  # Convert to months
            
            # Cumulative cash flow distribution: S_T ~ N(T*μ_C, T*σ_C²)
            cumulative_mean = T * mean_cashflow
            cumulative_std = math.sqrt(T) * std_cashflow if T > 0 else 0.0
            
            # Probability of not reaching goal
            if cumulative_std == 0:
                failure_prob = 1.0 if cumulative_mean < remaining else 0.0
            else:
                z = (remaining - cumulative_mean) / cumulative_std
                failure_prob = self._normal_cdf(z)
            
            # Expected shortfall for goal
            if cumulative_std == 0:
                expected_shortfall = abs(remaining - cumulative_mean) if cumulative_mean < remaining else 0.0
            else:
                expected_shortfall = self._compute_expected_shortfall(
                    cumulative_mean - remaining,
                    cumulative_std
                )
            
            goal_risks.append({
                "goal_id": goal.get("id"),
                "goal_name": goal.get("name"),
                "failure_probability": max(0.0, min(1.0, failure_prob)),
                "expected_shortfall": expected_shortfall,
                "months_to_goal": months_to_goal,
                "remaining_amount": remaining
            })
        
        return goal_risks
    
    def _compute_runway(
        self,
        mean_cashflow: float,
        std_cashflow: float
    ) -> float:
        """
        Compute expected runway (days until cash flow becomes negative).
        
        If mean_cashflow < 0, runway is 0.
        Otherwise, estimate based on probability distribution.
        """
        if mean_cashflow <= 0:
            return 0.0
        
        if std_cashflow == 0:
            return float('inf')  # Infinite runway if no variance
        
        # Simple approximation: days until 50% probability of negative
        # This is when mean - 0.67*std = 0 (roughly 25th percentile)
        days = (mean_cashflow / std_cashflow) * 30  # Convert to days
        
        return max(0.0, days)
    
    def stress_test(
        self,
        transactions: List[Dict],
        shock_scenarios: Dict[str, float],
        goals: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Stress test: Apply shocks and recompute risk.
        
        shock_scenarios example:
        {
            "rent": 1.1,  # 10% increase
            "income": 0.9,  # 10% decrease
            "dining": 0.8   # 20% decrease
        }
        """
        # Get base risk
        base_risk = self.analyze_risk(transactions, goals)
        
        # Apply shocks to transactions
        shocked_transactions = []
        for txn in transactions:
            txn_copy = txn.copy()
            category = txn.get("category") or "Uncategorized"
            
            if txn.get("transaction_type") == "income":
                if "income" in shock_scenarios:
                    txn_copy["amount"] = txn["amount"] * shock_scenarios["income"]
            else:
                if category in shock_scenarios:
                    txn_copy["amount"] = txn["amount"] * shock_scenarios[category]
            
            shocked_transactions.append(txn_copy)
        
        # Compute shocked risk
        shocked_risk = self.analyze_risk(shocked_transactions, goals)
        
        return {
            "base_risk": base_risk,
            "shocked_risk": shocked_risk,
            "delta": {
                "failure_probability": shocked_risk["failure_probability"] - base_risk["failure_probability"],
                "expected_shortfall": shocked_risk["expected_shortfall"] - base_risk["expected_shortfall"],
                "mean_cashflow": shocked_risk["mean_cashflow"] - base_risk["mean_cashflow"]
            },
            "scenarios": shock_scenarios
        }
    
    def _empty_risk_result(self) -> Dict:
        """Return empty risk result when no transactions."""
        return {
            "failure_probability": 0.0,
            "expected_shortfall": 0.0,
            "mean_cashflow": 0.0,
            "std_cashflow": 0.0,
            "risk_drivers": [],
            "goal_risks": [],
            "runway_days": 0.0,
            "income_stats": {"mean": 0.0, "variance": 0.0, "std": 0.0},
            "expense_stats": {"total_mean": 0.0, "total_variance": 0.0, "category_stats": {}}
        }

