"""
Probabilistic cash-flow risk.

Period cash flow is estimated from dated transactions, then scaled to a
monthly unit so the normal model is internally consistent:

    C ~ N(μ, σ²)
    μ = μ_I - Σ_k μ_k
    σ² = σ_I² + Σ_k σ_k²     (independent category shocks)

Horizon-T cumulative cash flow (T months):

    S_T ~ N(T μ, T σ²)
    P(S_T < 0) = Φ(-√T · μ / σ)
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import math

from app.services.money import largest_remainder_percents

WEEKS_PER_MONTH = 365.25 / 12.0 / 7.0
PRIOR_CV = 0.25


def _parse_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _normal_pdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


class CashFlowRiskAnalyzer:
    def analyze_risk(
        self,
        transactions: List[Dict],
        goals: Optional[List[Dict]] = None,
        horizon_days: int = 30,
    ) -> Dict:
        selected = self._select_sample(transactions)
        if not selected:
            return self._empty_risk_result()

        income_stats, expense_stats, mean_cashflow, var_cashflow = self._estimate_monthly(selected)
        std_cashflow = math.sqrt(var_cashflow) if var_cashflow > 0 else 0.0

        horizon_days = max(1, int(horizon_days or 30))
        months = horizon_days / 30.0
        horizon_mean = months * mean_cashflow
        horizon_std = math.sqrt(months) * std_cashflow if months > 0 else 0.0

        failure_prob = self._failure_probability(horizon_mean, horizon_std)
        expected_shortfall = self._expected_shortfall(horizon_mean, horizon_std)
        risk_drivers = self._risk_attribution(income_stats, expense_stats["category_stats"], var_cashflow)
        goal_risks = self._compute_goal_risks(goals or [], mean_cashflow, std_cashflow, horizon_days)
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
            "expense_stats": expense_stats,
        }

    def _select_sample(self, transactions: List[Dict]) -> List[Dict]:
        dated = []
        for txn in transactions:
            dt = _parse_date(txn.get("date"))
            if not dt:
                continue
            dated.append((dt, txn))
        if not dated:
            return []

        latest = max(dt for dt, _ in dated)
        # Drop decade-old OCR leftovers that would distort rates.
        dated = [(dt, txn) for dt, txn in dated if dt >= latest - timedelta(days=365 * 3)]
        if not dated:
            return []

        latest = max(dt for dt, _ in dated)
        for days in (90, 180, 365, 365 * 3):
            start = latest - timedelta(days=days)
            sample = [txn for dt, txn in dated if dt >= start]
            if len(sample) >= 8 or days == 365 * 3:
                return sample
        return [txn for _, txn in dated]

    def _estimate_monthly(
        self, transactions: List[Dict]
    ) -> Tuple[Dict, Dict, float, float]:
        dated = []
        for txn in transactions:
            dt = _parse_date(txn.get("date"))
            if dt:
                dated.append((dt, txn))
        dated.sort(key=lambda item: item[0])

        first, last = dated[0][0], dated[-1][0]
        span_days = max(1, (last - first).days + 1)
        scale = 30.0 / span_days

        weekly_income: Dict[Tuple[int, int], float] = defaultdict(float)
        weekly_expense: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        total_income = 0.0
        category_totals: Dict[str, float] = defaultdict(float)
        income_count = 0
        expense_count = 0

        for dt, txn in dated:
            key = dt.isocalendar()[:2]
            amount = abs(float(txn.get("amount") or 0.0))
            if (txn.get("transaction_type") or "").lower() == "income":
                weekly_income[key] += amount
                total_income += amount
                income_count += 1
            else:
                category = txn.get("category") or "Uncategorized"
                weekly_expense[key][category] += amount
                category_totals[category] += amount
                expense_count += 1

        week_keys = []
        cursor = first
        while cursor <= last:
            week_keys.append(cursor.isocalendar()[:2])
            cursor += timedelta(days=7)
        week_keys = sorted(set(week_keys))
        n_weeks = max(1, len(week_keys))

        income_weeks = [weekly_income.get(k, 0.0) for k in week_keys]
        mean_weekly_income = sum(income_weeks) / n_weeks
        var_weekly_income = self._sample_variance(income_weeks, mean_weekly_income, mean_weekly_income)

        income_stats = {
            "mean": mean_weekly_income * WEEKS_PER_MONTH,
            "variance": var_weekly_income * WEEKS_PER_MONTH,
            "std": math.sqrt(max(0.0, var_weekly_income * WEEKS_PER_MONTH)),
            "count": float(income_count),
            "sample_days": float(span_days),
        }
        # Rate-based mean is more stable than sparse weekly averages when
        # activity is clustered. Blend toward the calendar rate.
        rate_income = total_income * scale
        income_stats["mean"] = 0.5 * income_stats["mean"] + 0.5 * rate_income

        category_stats = {}
        total_mean = 0.0
        total_variance = 0.0
        for category, total in category_totals.items():
            weeks = [weekly_expense[k].get(category, 0.0) for k in week_keys]
            mean_weekly = sum(weeks) / n_weeks
            var_weekly = self._sample_variance(weeks, mean_weekly, mean_weekly)
            mean_month = 0.5 * (mean_weekly * WEEKS_PER_MONTH) + 0.5 * (total * scale)
            var_month = var_weekly * WEEKS_PER_MONTH
            std_month = math.sqrt(max(0.0, var_month))
            category_stats[category] = {
                "mean": mean_month,
                "variance": var_month,
                "std": std_month,
                "cv": (std_month / mean_month) if mean_month > 0 else 0.0,
                "count": sum(1 for w in weeks if w > 0),
            }
            total_mean += mean_month
            total_variance += var_month

        expense_stats = {
            "total_mean": total_mean,
            "total_variance": total_variance,
            "total_std": math.sqrt(total_variance) if total_variance > 0 else 0.0,
            "category_stats": category_stats,
        }

        mean_cashflow = income_stats["mean"] - total_mean
        var_cashflow = income_stats["variance"] + total_variance
        return income_stats, expense_stats, mean_cashflow, var_cashflow

    def _sample_variance(self, values: List[float], mean: float, level: float) -> float:
        n = len(values)
        prior = (PRIOR_CV * max(level, 0.0)) ** 2
        if n < 2:
            return prior
        empirical = sum((v - mean) ** 2 for v in values) / (n - 1)
        # Shrink noisy sample variance toward a CV prior.
        weight = n / (n + 4)
        return weight * empirical + (1 - weight) * prior

    def _failure_probability(self, mean: float, std: float) -> float:
        if std <= 1e-12:
            return 1.0 if mean < 0 else 0.0
        return max(0.0, min(1.0, _normal_cdf(-mean / std)))

    def _expected_shortfall(self, mean: float, std: float) -> float:
        """
        E[C | C < 0] for C ~ N(μ, σ²), reported as a positive shortfall.
        ES = μ - σ φ(z) / Φ(z),  z = -μ/σ.
        """
        if std <= 1e-12:
            return abs(mean) if mean < 0 else 0.0

        z = -mean / std
        cdf = _normal_cdf(z)
        if cdf < 1e-12:
            return 0.0
        es = mean - std * (_normal_pdf(z) / cdf)
        return abs(es) if es < 0 else 0.0

    def _risk_attribution(
        self,
        income_stats: Dict,
        category_stats: Dict[str, Dict],
        total_variance: float,
    ) -> List[Dict]:
        rows = []
        if income_stats.get("variance", 0) > 0:
            rows.append({
                "category": "Income",
                "variance": income_stats["variance"],
                "std": income_stats["std"],
                "mean": income_stats["mean"],
                "cv": (income_stats["std"] / income_stats["mean"]) if income_stats["mean"] > 0 else 0.0,
            })
        for category, stats in category_stats.items():
            rows.append({
                "category": category,
                "variance": stats["variance"],
                "std": stats["std"],
                "mean": stats["mean"],
                "cv": stats["cv"],
            })

        variances = [row["variance"] for row in rows]
        percents = largest_remainder_percents(variances)
        attributions = []
        for row, pct in zip(rows, percents):
            attributions.append({
                **row,
                "risk_share": pct / 100.0,
                "contribution": pct,
            })
        attributions.sort(key=lambda x: x["risk_share"], reverse=True)
        return attributions

    def _compute_goal_risks(
        self,
        goals: List[Dict],
        mean_cashflow: float,
        std_cashflow: float,
        horizon_days: int,
    ) -> List[Dict]:
        goal_risks = []
        T = max(horizon_days, 1) / 30.0

        for goal in goals:
            current = float(goal.get("current_amount") or 0.0)
            target = float(goal.get("target_amount") or 0.0)
            remaining = max(0.0, target - current)

            if remaining <= 0:
                goal_risks.append({
                    "goal_id": goal.get("id") or 0,
                    "goal_name": goal.get("name") or "Goal",
                    "failure_probability": 0.0,
                    "expected_shortfall": 0.0,
                    "months_to_goal": 0.0,
                    "remaining_amount": 0.0,
                })
                continue

            if mean_cashflow > 0:
                months_to_goal = remaining / mean_cashflow
            else:
                months_to_goal = 999.0

            cumulative_mean = T * mean_cashflow
            cumulative_std = math.sqrt(T) * std_cashflow if T > 0 else 0.0

            if cumulative_std <= 1e-12:
                failure_prob = 1.0 if cumulative_mean < remaining else 0.0
                expected_shortfall = max(0.0, remaining - cumulative_mean)
            else:
                z = (remaining - cumulative_mean) / cumulative_std
                failure_prob = max(0.0, min(1.0, _normal_cdf(z)))
                expected_shortfall = self._expected_shortfall(
                    cumulative_mean - remaining,
                    cumulative_std,
                )

            goal_risks.append({
                "goal_id": goal.get("id") or 0,
                "goal_name": goal.get("name") or "Goal",
                "failure_probability": failure_prob,
                "expected_shortfall": expected_shortfall,
                "months_to_goal": months_to_goal,
                "remaining_amount": remaining,
            })
        return goal_risks

    def _compute_runway(self, mean_cashflow: float, std_cashflow: float) -> float:
        if mean_cashflow <= 0:
            return 0.0
        if std_cashflow <= 1e-12:
            return 3650.0
        return max(0.0, (mean_cashflow / std_cashflow) * 30.0)

    def stress_test(
        self,
        transactions: List[Dict],
        shock_scenarios: Dict[str, float],
        goals: Optional[List[Dict]] = None,
        horizon_days: int = 30,
    ) -> Dict:
        normalized = {str(k).strip().lower(): float(v) for k, v in (shock_scenarios or {}).items()}
        base_risk = self.analyze_risk(transactions, goals, horizon_days)

        shocked = []
        for txn in transactions:
            copy = dict(txn)
            category = (copy.get("category") or "Uncategorized")
            txn_type = (copy.get("transaction_type") or "").lower()
            amount = float(copy.get("amount") or 0.0)
            if txn_type == "income":
                factor = normalized.get("income", 1.0)
            else:
                factor = normalized.get(category.lower(), 1.0)
            copy["amount"] = amount * factor
            shocked.append(copy)

        shocked_risk = self.analyze_risk(shocked, goals, horizon_days)
        return {
            "base_risk": base_risk,
            "shocked_risk": shocked_risk,
            "delta": {
                "failure_probability": shocked_risk["failure_probability"] - base_risk["failure_probability"],
                "expected_shortfall": shocked_risk["expected_shortfall"] - base_risk["expected_shortfall"],
                "mean_cashflow": shocked_risk["mean_cashflow"] - base_risk["mean_cashflow"],
            },
            "scenarios": shock_scenarios,
        }

    def _empty_risk_result(self) -> Dict:
        return {
            "failure_probability": 0.0,
            "expected_shortfall": 0.0,
            "mean_cashflow": 0.0,
            "std_cashflow": 0.0,
            "risk_drivers": [],
            "goal_risks": [],
            "runway_days": 0.0,
            "income_stats": {"mean": 0.0, "variance": 0.0, "std": 0.0, "count": 0.0, "sample_days": 0.0},
            "expense_stats": {"total_mean": 0.0, "total_variance": 0.0, "total_std": 0.0, "category_stats": {}},
        }
