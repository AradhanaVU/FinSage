# Probabilistic Cash-Flow Risk Analysis: Mathematical Foundation

This document explains the mathematical models used in the cash-flow risk analysis engine.

## Core Concept

Instead of treating cash flow as a fixed number, we model it as a **random variable** with a probability distribution.

## 1. Cash Flow as a Random Variable

**Monthly Net Cash Flow:**
```
C_t = I_t - E_t
```

Where:
- `I_t` = Income in month `t` (random variable)
- `E_t` = Total expenses in month `t` (random variable)
- `C_t` = Net cash flow (random variable)

## 2. Income Distribution

**Model:**
```
I_t ~ N(μ_I, σ_I²)
```

Where:
- `μ_I` = Mean monthly income
- `σ_I²` = Variance of monthly income

**Computation:**
- `μ_I` = mean(income_transactions)
- `σ_I²` = variance(income_transactions)

## 3. Expense Distribution

**Breakdown by Category:**
```
E_t = Σ E_k,t
```

Where each category `k` has:
```
E_k,t ~ N(μ_k, σ_k²)
```

**Computation:**
- `μ_k` = mean(expenses in category k)
- `σ_k²` = variance(expenses in category k)

**Total Expense Variance:**
```
σ_E² = Σ σ_k²
```

This is where **volatility** lives - categories with high variance contribute more to risk.

## 4. Net Cash Flow Distribution

Since income and expenses are sums of normal random variables:

```
C_t ~ N(μ_C, σ_C²)
```

Where:
- `μ_C = μ_I - Σ μ_k` (mean net cash flow)
- `σ_C² = σ_I² + Σ σ_k²` (variance of net cash flow)

## 5. Failure Probability

**Definition:** Probability that cash flow becomes negative

```
P(failure) = P(C_t < 0) = Φ(-μ_C / σ_C)
```

Where `Φ` is the standard normal cumulative distribution function (CDF).

**Interpretation:**
- If `μ_C > 0` and `σ_C` is small → low failure probability
- If `μ_C < 0` → high failure probability
- If `μ_C > 0` but `σ_C` is large → moderate failure probability (volatility risk)

## 6. Expected Shortfall (Tail Risk)

**Definition:** Expected loss when failure occurs

```
ES = E[C_t | C_t < 0]
```

For normal distribution:
```
ES = μ_C - σ_C * (φ(z) / Φ(z))
```

Where:
- `z = -μ_C / σ_C`
- `φ(z)` = standard normal PDF
- `Φ(z)` = standard normal CDF

**Interpretation:** "If things go wrong, how bad do they get?"

## 7. Risk Attribution

**Question:** "What causes my risk?"

Since variance adds linearly:
```
σ_C² = σ_I² + Σ σ_k²
```

**Risk Share of Category k:**
```
Risk Share_k = σ_k² / σ_C²
```

**Example:**
- Dining: σ² = 100, Total: σ² = 500
- Risk Share = 100/500 = 20%
- "Dining contributes 20% of your cash-flow risk"

This identifies which categories drive volatility.

## 8. Coefficient of Variation (Normalized Risk)

**Definition:**
```
CV_k = σ_k / μ_k
```

**Why it matters:**
- $50 grocery volatility ≠ $50 travel volatility
- CV normalizes by spending level
- High CV = high relative volatility (risky even if small)

## 9. Goal-Conditioned Risk

**Question:** "What's the probability I'll miss my goal?"

**Cumulative Cash Flow:**
```
S_T = Σ C_t (from t=1 to T)
```

If monthly cash flows are independent:
```
S_T ~ N(T * μ_C, T * σ_C²)
```

**Goal Failure Probability:**
```
P(goal failure) = P(S_T < G) = Φ((G - T*μ_C) / (√T * σ_C))
```

Where:
- `G` = remaining amount needed for goal
- `T` = months to goal deadline

**Interpretation:** Risk is relative to goals, not absolute.

## 10. Runway Calculation

**Definition:** Expected days until cash flow becomes negative

**Simple approximation:**
```
runway_days = (μ_C / σ_C) * 30
```

When `μ_C / σ_C` drops, runway shortens.

## 11. Stress Testing

**Apply shocks:**
- Rent: `μ_rent' = 1.1 * μ_rent` (10% increase)
- Income: `μ_I' = 0.9 * μ_I` (10% decrease)

**Recompute:**
- New `μ_C'` and `σ_C'`
- New failure probabilities
- Compare to baseline

**Output:** "If rent increases 10%, failure probability increases from 18% → 34%"

## Implementation Notes

1. **Normal Distribution Assumption:**
   - Reasonable for aggregated cash flows (Central Limit Theorem)
   - May need adjustments for heavy-tailed distributions

2. **Independence Assumption:**
   - Monthly cash flows assumed independent
   - Can be extended with autocorrelation if needed

3. **Variance Estimation:**
   - Requires sufficient historical data
   - Minimum 3-5 transactions per category recommended

4. **Time Horizon:**
   - Short-term (30 days): More accurate
   - Long-term (180+ days): More uncertain, but useful for planning

## Mathematical Properties

- **Additivity:** Risk attribution is mathematically clean (variances add)
- **Scalability:** Works with any number of categories
- **Interpretability:** Every number has clear meaning
- **Testability:** Can validate against historical outcomes

## References

- Standard normal CDF: Abramowitz & Stegun approximation
- Expected shortfall: Standard formula for normal distributions
- Risk attribution: Variance decomposition

