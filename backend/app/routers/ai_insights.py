from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.ai.categorizer import TransactionCategorizer
from app.ai.pattern_detector import PatternDetector
from app.ai.forecaster import SpendingForecaster
from collections import defaultdict

router = APIRouter()
categorizer = TransactionCategorizer()
pattern_detector = PatternDetector()
forecaster = SpendingForecaster()

@router.get("/spending-analysis", response_model=List[schemas.SpendingAnalysis])
async def get_spending_analysis(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get spending analysis by category."""
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.transaction_type == "expense",
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).all()
    
    # Group by category
    category_data = defaultdict(lambda: {"total": 0.0, "count": 0, "amounts": []})
    
    for txn in transactions:
        category = txn.category or "Uncategorized"
        category_data[category]["total"] += abs(txn.amount)
        category_data[category]["count"] += 1
        category_data[category]["amounts"].append(abs(txn.amount))
    
    total_spending = sum(data["total"] for data in category_data.values())
    
    analysis = []
    for category, data in category_data.items():
        avg_amount = data["total"] / data["count"] if data["count"] > 0 else 0
        percentage = (data["total"] / total_spending * 100) if total_spending > 0 else 0
        
        # Determine trend (simplified)
        trend = "stable"
        if len(data["amounts"]) >= 2:
            recent_avg = sum(data["amounts"][-3:]) / min(3, len(data["amounts"]))
            older_avg = sum(data["amounts"][:-3]) / max(1, len(data["amounts"]) - 3) if len(data["amounts"]) > 3 else recent_avg
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
        
        analysis.append(schemas.SpendingAnalysis(
            category=category,
            total_amount=round(data["total"], 2),
            transaction_count=data["count"],
            average_amount=round(avg_amount, 2),
            trend=trend,
            percentage_of_total=round(percentage, 2)
        ))
    
    return sorted(analysis, key=lambda x: x.total_amount, reverse=True)

@router.get("/patterns", response_model=List[schemas.PatternDetection])
async def get_spending_patterns(
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Detect spending patterns and anomalies."""
    start_date = datetime.now() - timedelta(days=days)
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.date >= start_date
    ).all()
    
    # Convert to dict format
    transaction_dicts = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    patterns = pattern_detector.detect_patterns(transaction_dicts)
    
    return [
        schemas.PatternDetection(
            category=p.get("category", "General"),
            pattern_type=p.get("pattern_type", "unknown"),
            description=p.get("description", ""),
            impact=p.get("trend", "unknown")
        )
        for p in patterns
    ]

@router.get("/forecast", response_model=List[schemas.SpendingForecast])
async def get_spending_forecast(
    days_ahead: int = 30,
    db: Session = Depends(get_db)
):
    """Get spending forecast for the next N days."""
    start_date = datetime.now() - timedelta(days=90)
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.transaction_type == "expense",
        models.Transaction.date >= start_date
    ).all()
    
    transaction_dicts = [
        {
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    forecasts = forecaster.forecast(transaction_dicts, days_ahead)
    
    return [
        schemas.SpendingForecast(
            date=datetime.fromisoformat(f["date"]),
            predicted_amount=f["predicted_amount"],
            confidence_interval_lower=f["confidence_interval_lower"],
            confidence_interval_upper=f["confidence_interval_upper"]
        )
        for f in forecasts
    ]

@router.get("/anomalies", response_model=List[schemas.AnomalyDetection])
async def get_anomalies(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Detect anomalous transactions."""
    start_date = datetime.now() - timedelta(days=days)
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.date >= start_date
    ).all()
    
    transaction_dicts = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    patterns = pattern_detector.detect_patterns(transaction_dicts)
    anomalies = [p for p in patterns if p.get("pattern_type") == "anomaly"]
    
    return [
        schemas.AnomalyDetection(
            transaction_id=a.get("transaction_id", 0),
            anomaly_score=round(a.get("anomaly_score", 0), 2),
            reason=a.get("description", "Unusual transaction amount"),
            severity=a.get("severity", "medium")
        )
        for a in anomalies
    ]


