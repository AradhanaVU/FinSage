from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.ai.alert_generator import AlertGenerator

router = APIRouter()
alert_generator = AlertGenerator()

@router.get("/", response_model=List[schemas.AlertResponse])
async def get_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all alerts for the user."""
    query = db.query(models.Alert).filter(
        models.Alert.user_id == 1  # TODO: Auth
    )
    
    if unread_only:
        query = query.filter(models.Alert.read == False)
    
    alerts = query.order_by(models.Alert.created_at.desc()).all()
    return alerts

@router.post("/generate")
async def generate_alerts(db: Session = Depends(get_db)):
    """Generate new alerts based on current financial data."""
    user_id = 1  # TODO: Auth
    
    # Get recent transactions
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= datetime.now() - timedelta(days=90)
    ).all()
    
    # Get goals
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).all()
    
    # Calculate current balance
    transactions_list = [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "merchant": t.merchant,
            "transaction_type": t.transaction_type,
            "date": t.date.isoformat() if t.date else None
        }
        for t in transactions
    ]
    
    goals_list = [
        {
            "id": g.id,
            "name": g.name,
            "current_amount": g.current_amount,
            "target_amount": g.target_amount
        }
        for g in goals
    ]
    
    # Calculate balance
    current_balance = sum(
        t.amount if t.transaction_type == "income" else -abs(t.amount)
        for t in transactions
    )
    
    monthly_income = sum(
        t.amount for t in transactions
        if t.transaction_type == "income" and
        t.date >= datetime.now() - timedelta(days=30)
    )
    
    # Generate alerts
    alerts = alert_generator.generate_alerts(
        transactions_list,
        goals_list,
        current_balance,
        monthly_income
    )
    
    # Get existing alerts from the last 24 hours to avoid duplicates
    recent_cutoff = datetime.now() - timedelta(hours=24)
    existing_alerts = db.query(models.Alert).filter(
        models.Alert.user_id == user_id,
        models.Alert.created_at >= recent_cutoff
    ).all()
    
    # Create a set of existing alert signatures for duplicate detection
    existing_signatures = set()
    for existing in existing_alerts:
        # Create a signature based on alert type and title
        signature = f"{existing.alert_type}:{existing.title}"
        existing_signatures.add(signature)
    
    # Save only new alerts (not duplicates)
    db_alerts = []
    skipped_count = 0
    for alert_data in alerts:
        # Create signature for this alert
        alert_signature = f"{alert_data.get('alert_type')}:{alert_data.get('title')}"
        
        # Skip if this alert already exists
        if alert_signature in existing_signatures:
            skipped_count += 1
            continue
        
        # Rename 'metadata' key to 'alert_metadata' for database
        alert_dict = alert_data.copy()
        if 'metadata' in alert_dict:
            alert_dict['alert_metadata'] = alert_dict.pop('metadata')
        db_alert = models.Alert(
            user_id=user_id,
            **alert_dict
        )
        db.add(db_alert)
        db_alerts.append(db_alert)
        # Add to existing signatures to avoid duplicates within this batch
        existing_signatures.add(alert_signature)
    
    db.commit()
    
    for alert in db_alerts:
        db.refresh(alert)
    
    return {
        "generated": len(db_alerts), 
        "skipped": skipped_count,
        "alerts": db_alerts
    }

@router.patch("/{alert_id}/read")
async def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as read."""
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == 1  # TODO: Auth
    ).first()
    
    if not alert:
        return {"message": "Alert not found"}
    
    alert.read = True
    db.commit()
    
    return {"message": "Alert marked as read"}

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert."""
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == 1  # TODO: Auth
    ).first()
    
    if not alert:
        return {"message": "Alert not found"}
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Alert deleted"}

