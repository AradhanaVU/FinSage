from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class PatternDetector:
    def __init__(self):
        pass
    
    def detect_patterns(self, transactions: List[Dict]) -> List[Dict]:
        """
        Detect spending patterns from transaction history.
        Returns list of detected patterns with descriptions.
        """
        patterns = []
        
        if not transactions:
            return patterns
        
        # Group by category
        category_data = defaultdict(list)
        for txn in transactions:
            if txn.get("category"):
                category_data[txn["category"]].append(txn)
        
        # Detect frequency patterns
        for category, txns in category_data.items():
            if len(txns) < 3:
                continue
            
            # Calculate average amount
            amounts = [t["amount"] for t in txns]
            avg_amount = statistics.mean(amounts)
            
            # Detect trend
            trend = self._detect_trend(txns)
            
            # Detect frequency
            frequency = self._detect_frequency(txns)
            
            patterns.append({
                "category": category,
                "pattern_type": "recurring" if frequency else "irregular",
                "description": f"Average spending of ${avg_amount:.2f} on {category}",
                "frequency": frequency,
                "trend": trend,
                "average_amount": avg_amount,
                "transaction_count": len(txns)
            })
        
        # Detect anomalies
        anomalies = self._detect_anomalies(transactions)
        patterns.extend(anomalies)
        
        return patterns
    
    def _detect_trend(self, transactions: List[Dict]) -> str:
        """Detect if spending is increasing, decreasing, or stable."""
        if len(transactions) < 3:
            return "insufficient_data"
        
        # Sort by date
        sorted_txns = sorted(transactions, key=lambda x: x.get("date", datetime.now()))
        # Use absolute values for trend detection (expenses are negative)
        amounts = [abs(t["amount"]) for t in sorted_txns]
        
        # Simple trend detection: compare first half vs second half
        mid = len(amounts) // 2
        first_half_avg = statistics.mean(amounts[:mid])
        second_half_avg = statistics.mean(amounts[mid:])
        
        # Handle division by zero: if first_half_avg is 0
        if first_half_avg == 0:
            # If second half is also 0, it's stable
            if second_half_avg == 0:
                return "stable"
            # If second half has spending, it's increasing (from 0 to something)
            else:
                return "increasing"
        
        change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _detect_frequency(self, transactions: List[Dict]) -> str:
        """Detect if transactions occur daily, weekly, or monthly."""
        if len(transactions) < 2:
            return None
        
        sorted_txns = sorted(transactions, key=lambda x: x.get("date", datetime.now()))
        dates = [t.get("date") for t in sorted_txns if t.get("date")]
        
        if len(dates) < 2:
            return None
        
        # Calculate average days between transactions
        intervals = []
        for i in range(1, len(dates)):
            if isinstance(dates[i], str):
                dates[i] = datetime.fromisoformat(dates[i].replace('Z', '+00:00'))
            if isinstance(dates[i-1], str):
                dates[i-1] = datetime.fromisoformat(dates[i-1].replace('Z', '+00:00'))
            
            if isinstance(dates[i], datetime) and isinstance(dates[i-1], datetime):
                interval = (dates[i] - dates[i-1]).days
                intervals.append(interval)
        
        if not intervals:
            return None
        
        avg_interval = statistics.mean(intervals)
        
        if avg_interval <= 2:
            return "daily"
        elif avg_interval <= 8:
            return "weekly"
        elif avg_interval <= 35:
            return "monthly"
        else:
            return "irregular"
    
    def _detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """Detect anomalous transactions using statistical methods."""
        anomalies = []
        
        if len(transactions) < 5:
            return anomalies
        
        # Group by category for better anomaly detection
        category_data = defaultdict(list)
        for txn in transactions:
            if txn.get("category"):
                category_data[txn["category"]].append(txn)
        
        for category, txns in category_data.items():
            if len(txns) < 3:
                continue
            
            amounts = [abs(t["amount"]) for t in txns]
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if stdev == 0:
                continue
            
            # Transactions more than 2 standard deviations from mean are anomalies
            threshold = mean + (2 * stdev)
            
            for txn in txns:
                if abs(txn["amount"]) > threshold:
                    anomaly_score = (abs(txn["amount"]) - mean) / stdev
                    anomalies.append({
                        "category": category,
                        "pattern_type": "anomaly",
                        "description": f"Unusually large transaction: ${txn['amount']:.2f}",
                        "transaction_id": txn.get("id"),
                        "anomaly_score": anomaly_score,
                        "severity": "high" if anomaly_score > 3 else "medium"
                    })
        
        return anomalies


