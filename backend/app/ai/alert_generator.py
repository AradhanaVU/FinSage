from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class AlertGenerator:
    def __init__(self):
        pass
    
    def generate_alerts(
        self,
        transactions: List[Dict],
        goals: List[Dict],
        current_balance: float = 0.0,
        monthly_income: float = 0.0
    ) -> List[Dict]:
        """
        Generate personalized alerts based on spending patterns and goals.
        """
        alerts = []
        
        if not transactions:
            return alerts
        
        # Unusual spending alert
        unusual_spending = self._detect_unusual_spending(transactions)
        if unusual_spending:
            alerts.append(unusual_spending)
        
        # Cash shortage alert
        cash_shortage = self._detect_cash_shortage(
            transactions, current_balance, monthly_income
        )
        if cash_shortage:
            alerts.append(cash_shortage)
        
        # Goal milestone alerts
        goal_alerts = self._check_goal_milestones(goals)
        alerts.extend(goal_alerts)
        
        # High spending category alert
        category_alerts = self._detect_high_spending_categories(transactions)
        alerts.extend(category_alerts)
        
        # Subscription recommendations
        subscription_alerts = self._detect_subscription_opportunities(transactions)
        alerts.extend(subscription_alerts)
        
        return alerts
    
    def _detect_unusual_spending(self, transactions: List[Dict]) -> Dict:
        """Detect unusually large transactions."""
        if len(transactions) < 5:
            return None
        
        amounts = [abs(t["amount"]) for t in transactions]
        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts) if len(amounts) > 1 else mean * 0.3
        
        recent_transactions = sorted(
            transactions,
            key=lambda x: self._parse_date(x.get("date", datetime.now())),
            reverse=True
        )[:10]
        
        for txn in recent_transactions:
            if abs(txn["amount"]) > mean + (2 * stdev):
                return {
                    "alert_type": "unusual_spending",
                    "title": "Unusual Spending Detected",
                    "message": f"Large transaction detected: ${txn['amount']:.2f} at {txn.get('merchant', 'Unknown')}. This is significantly higher than your average spending.",
                    "severity": "warning",
                    "metadata": {
                        "transaction_id": txn.get("id"),
                        "amount": txn["amount"],
                        "category": txn.get("category")
                    }
                }
        
        return None
    
    def _detect_cash_shortage(
        self,
        transactions: List[Dict],
        current_balance: float,
        monthly_income: float
    ) -> Dict:
        """Detect potential cash flow issues."""
        if monthly_income == 0:
            return None
        
        # Calculate monthly expenses
        recent_transactions = [
            t for t in transactions
            if self._parse_date(t.get("date", datetime.now())) > datetime.now() - timedelta(days=30)
        ]
        
        monthly_expenses = sum(abs(t["amount"]) for t in recent_transactions if t.get("transaction_type") == "expense")
        
        # Project future expenses
        if len(recent_transactions) > 0:
            daily_average = monthly_expenses / 30
            projected_monthly = daily_average * 30
            
            # Check if balance can cover projected expenses
            if current_balance < projected_monthly * 0.5:  # Less than 2 weeks of expenses
                return {
                    "alert_type": "cash_shortage",
                    "title": "Low Cash Balance Warning",
                    "message": f"Your current balance (${current_balance:.2f}) may not cover projected monthly expenses (${projected_monthly:.2f}). Consider reducing spending or increasing income.",
                    "severity": "warning",
                    "metadata": {
                        "current_balance": current_balance,
                        "projected_expenses": projected_monthly
                    }
                }
        
        return None
    
    def _check_goal_milestones(self, goals: List[Dict]) -> List[Dict]:
        """Check if goals have reached milestones."""
        alerts = []
        
        for goal in goals:
            current = goal.get("current_amount", 0)
            target = goal.get("target_amount", 1)
            progress = (current / target) * 100 if target > 0 else 0
            
            # 25%, 50%, 75%, 100% milestones
            milestones = [25, 50, 75, 100]
            for milestone in milestones:
                if 95 <= progress < milestone + 5:  # Within 5% of milestone
                    alerts.append({
                        "alert_type": "goal_milestone",
                        "title": f"Goal Milestone: {goal.get('name', 'Goal')}",
                        "message": f"Congratulations! You've reached {milestone}% of your goal '{goal.get('name')}'. Keep it up!",
                        "severity": "info",
                        "metadata": {
                            "goal_id": goal.get("id"),
                            "milestone": milestone,
                            "progress": progress
                        }
                    })
                    break
        
        return alerts
    
    def _detect_high_spending_categories(self, transactions: List[Dict]) -> List[Dict]:
        """Alert on high spending in specific categories."""
        alerts = []
        
        category_totals = defaultdict(float)
        for txn in transactions:
            if txn.get("category") and txn.get("transaction_type") == "expense":
                category_totals[txn["category"]] += abs(txn["amount"])
        
        total_spending = sum(category_totals.values())
        if total_spending == 0:
            return alerts
        
        for category, amount in category_totals.items():
            percentage = (amount / total_spending) * 100
            if percentage > 30:  # More than 30% of spending
                alerts.append({
                    "alert_type": "recommendation",
                    "title": f"High Spending in {category}",
                    "message": f"You're spending {percentage:.1f}% of your total expenses on {category}. Consider reviewing this category for potential savings.",
                    "severity": "info",
                    "metadata": {
                        "category": category,
                        "amount": amount,
                        "percentage": percentage
                    }
                })
        
        return alerts
    
    def _detect_subscription_opportunities(self, transactions: List[Dict]) -> List[Dict]:
        """Detect potential subscription savings."""
        alerts = []
        
        # Look for recurring transactions
        category_data = defaultdict(list)
        for txn in transactions:
            if txn.get("category"):
                category_data[txn["category"]].append(txn)
        
        for category, txns in category_data.items():
            if len(txns) >= 3:  # Potential recurring
                amounts = [abs(t["amount"]) for t in txns]
                if len(set(amounts)) <= 2:  # Similar amounts (likely subscription)
                    avg_amount = statistics.mean(amounts)
                    alerts.append({
                        "alert_type": "recommendation",
                        "title": f"Recurring Expense: {category}",
                        "message": f"You have a recurring expense of approximately ${avg_amount:.2f} for {category}. Review if this subscription is still needed or if there are cheaper alternatives.",
                        "severity": "info",
                        "metadata": {
                            "category": category,
                            "average_amount": avg_amount,
                            "frequency": "monthly"
                        }
                    })
        
        return alerts
    
    def _parse_date(self, date_value) -> datetime:
        """Parse date from various formats."""
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                return datetime.now()
        return datetime.now()


