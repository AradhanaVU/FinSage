from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.ai.categorizer import TransactionCategorizer
from app.services.goal_tracker import GoalTracker

router = APIRouter()
categorizer = TransactionCategorizer()
goal_tracker = GoalTracker()  # Create instance

@router.post("/", response_model=schemas.TransactionResponse)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new transaction and auto-categorize it."""
    # Auto-categorize using AI (pass transaction_type for better accuracy)
    category, subcategory, confidence = categorizer.categorize(
        transaction.description,
        transaction.amount,
        transaction.transaction_type
    )
    
    # Ensure expenses are stored as negative amounts
    transaction_data = transaction.dict()
    if transaction_data.get("transaction_type") == "expense" and transaction_data.get("amount", 0) > 0:
        transaction_data["amount"] = -abs(transaction_data["amount"])
    
    db_transaction = models.Transaction(
        **transaction_data,
        category=category,
        subcategory=subcategory,
        ai_categorized=True,
        confidence_score=confidence,
        user_id=1  # TODO: Get from authentication
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Automatically update goal progress
    try:
        goal_tracker.update_all_goals(user_id=1, db=db)  # TODO: Get from auth
        print(f"✓ Updated goals after transaction creation")  # Debug log
    except Exception as e:
        import traceback
        print(f"❌ Error updating goals: {e}")
        traceback.print_exc()  # Show full error
    
    return db_transaction

@router.get("/", response_model=List[schemas.TransactionResponse])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get all transactions with optional filters."""
    query = db.query(models.Transaction).filter(models.Transaction.user_id == 1)  # TODO: Auth
    
    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    transactions = query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()
    return transactions

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific transaction."""
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == 1  # TODO: Auth
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    """Update a transaction."""
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == 1  # TODO: Auth
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Re-categorize if description changed
    if transaction.description != db_transaction.description:
        category, subcategory, confidence = categorizer.categorize(
            transaction.description,
            transaction.amount,
            transaction.transaction_type or db_transaction.transaction_type
        )
        db_transaction.category = category
        db_transaction.subcategory = subcategory
        db_transaction.confidence_score = confidence
    
    for key, value in transaction.dict().items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    # Automatically update goal progress
    try:
        goal_tracker.update_all_goals(user_id=1, db=db)  # TODO: Get from auth
    except Exception as e:
        print(f"Error updating goals: {e}")
    
    return db_transaction

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction."""
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == 1  # TODO: Auth
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    
    # Automatically update goal progress
    try:
        goal_tracker.update_all_goals(user_id=1, db=db)  # TODO: Get from auth
    except Exception as e:
        print(f"Error updating goals: {e}")
    
    return {"message": "Transaction deleted"}

@router.post("/batch", response_model=List[schemas.TransactionResponse])
async def create_transactions_batch(
    transactions: List[schemas.TransactionCreate],
    db: Session = Depends(get_db)
):
    """Create multiple transactions at once with batch categorization."""
    db_transactions = []
    
    # Batch categorize
    transaction_dicts = [t.dict() for t in transactions]
    categorized = categorizer.batch_categorize(transaction_dicts)
    
    for txn_data in categorized:
        db_transaction = models.Transaction(
            **{k: v for k, v in txn_data.items() if k != "category" and k != "subcategory" and k != "confidence_score" and k != "ai_categorized"},
            category=txn_data.get("category"),
            subcategory=txn_data.get("subcategory"),
            ai_categorized=txn_data.get("ai_categorized", True),
            confidence_score=txn_data.get("confidence_score"),
            user_id=1  # TODO: Auth
        )
        db.add(db_transaction)
        db_transactions.append(db_transaction)
    
    db.commit()
    
    for txn in db_transactions:
        db.refresh(txn)
    
    # Automatically update goal progress
    try:
        goal_tracker.update_all_goals(user_id=1, db=db)  # TODO: Get from auth
    except Exception as e:
        print(f"Error updating goals: {e}")
    
    return db_transactions

