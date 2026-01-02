from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# numpy is optional - only used if available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

class SpendingForecaster:
    def __init__(self):
        pass
    
    def forecast(self, transactions: List[Dict], days_ahead: int = 30) -> List[Dict]:
        """
        Forecast future spending based on historical patterns.
        Returns list of forecasted dates with predicted amounts.
        """
        if not transactions:
            return []
        
        forecasts = []
        
        # Group transactions by category
        category_data = defaultdict(list)
        for txn in transactions:
            if txn.get("category") and txn.get("date"):
                category_data[txn["category"]].append(txn)
        
        # Forecast for each category
        for category, txns in category_data.items():
            if len(txns) < 3:
                continue
            
            # Sort by date
            sorted_txns = sorted(txns, key=lambda x: self._parse_date(x.get("date")))
            
            # Extract time series data
            dates = [self._parse_date(t.get("date")) for t in sorted_txns]
            amounts = [abs(t["amount"]) for t in sorted_txns]
            
            # Simple moving average forecast
            window_size = min(7, len(amounts))
            recent_avg = statistics.mean(amounts[-window_size:])
            
            # Calculate trend
            if len(amounts) >= 2:
                trend = (amounts[-1] - amounts[0]) / len(amounts)
            else:
                trend = 0
            
            # Generate forecasts
            last_date = dates[-1] if dates else datetime.now()
            for i in range(1, days_ahead + 1):
                forecast_date = last_date + timedelta(days=i)
                
                # Adjust for trend
                predicted_amount = recent_avg + (trend * i)
                
                # Calculate confidence intervals (simplified)
                stdev = statistics.stdev(amounts) if len(amounts) > 1 else recent_avg * 0.2
                confidence_lower = max(0, predicted_amount - (1.96 * stdev))
                confidence_upper = predicted_amount + (1.96 * stdev)
                
                forecasts.append({
                    "date": forecast_date.isoformat(),
                    "category": category,
                    "predicted_amount": round(predicted_amount, 2),
                    "confidence_interval_lower": round(confidence_lower, 2),
                    "confidence_interval_upper": round(confidence_upper, 2)
                })
        
        # Aggregate by date
        aggregated = self._aggregate_forecasts(forecasts)
        
        return aggregated
    
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
    
    def _aggregate_forecasts(self, forecasts: List[Dict]) -> List[Dict]:
        """Aggregate forecasts by date."""
        date_groups = defaultdict(list)
        
        for forecast in forecasts:
            date_key = forecast["date"][:10]  # Just the date part
            date_groups[date_key].append(forecast)
        
        aggregated = []
        for date_key, forecasts_for_date in sorted(date_groups.items()):
            total_predicted = sum(f["predicted_amount"] for f in forecasts_for_date)
            total_lower = sum(f["confidence_interval_lower"] for f in forecasts_for_date)
            total_upper = sum(f["confidence_interval_upper"] for f in forecasts_for_date)
            
            aggregated.append({
                "date": date_key,
                "predicted_amount": round(total_predicted, 2),
                "confidence_interval_lower": round(total_lower, 2),
                "confidence_interval_upper": round(total_upper, 2),
                "categories": [f["category"] for f in forecasts_for_date]
            })
        
        return aggregated

