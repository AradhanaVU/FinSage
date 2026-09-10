from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.ai.categorizer import TransactionCategorizer
from app.services.goal_tracker import GoalTracker
from app.services.money import signed_amount
from app.deps import get_current_user

router = APIRouter()
categorizer = TransactionCategorizer()
goal_tracker = GoalTracker()


def _lookup_learned_category(
    db: Session,
    user_id: int,
    description: str,
    merchant: Optional[str],
) -> Optional[models.Transaction]:
    """Reuse a user's previous manual label for the same merchant or description."""
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.ai_categorized.is_(False),
        models.Transaction.category.isnot(None),
    )
    if merchant and merchant.strip():
        match = query.filter(models.Transaction.merchant == merchant.strip()).order_by(
            models.Transaction.created_at.desc()
        ).first()
        if match:
            return match

    normalized = (description or "").strip().lower()
    if not normalized:
        return None
    candidates = query.order_by(models.Transaction.created_at.desc()).limit(200).all()
    for txn in candidates:
        if (txn.description or "").strip().lower() == normalized:
            return txn
    return None


def _resolve_category(
    db: Session,
    user_id: int,
    description: str,
    amount: float,
    transaction_type: str,
    merchant: Optional[str],
    user_category: Optional[str],
    user_subcategory: Optional[str],
):
    if user_category:
        return user_category, user_subcategory, 1.0, False

    learned = _lookup_learned_category(db, user_id, description, merchant)
    if learned:
        return learned.category, learned.subcategory or user_subcategory, 0.97, False

    category, subcategory, confidence = categorizer.categorize(
        description, amount, transaction_type
    )
    return category, subcategory, confidence, True


def _refresh_goals(db: Session, user_id: int):
    try:
        goal_tracker.update_all_goals(user_id=user_id, db=db)
    except Exception as e:
        print(f"Error updating goals: {e}")


@router.get("/categories")
async def list_categories(
    transaction_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
):
    if transaction_type:
        return {"categories": categorizer.get_categories_by_type(transaction_type)}
    return {"categories": categorizer.get_available_categories()}


@router.get("/suggest", response_model=schemas.CategorySuggestion)
async def suggest_category(
    description: str = Query(..., min_length=1),
    amount: float = 0.0,
    transaction_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
):
    result = categorizer.score_categories(description, amount, transaction_type)
    return schemas.CategorySuggestion(
        category=result["category"],
        subcategory=result.get("subcategory"),
        confidence=result["confidence"],
        probabilities=result.get("probabilities") or {},
        matched_phrases=result.get("matched_phrases") or [],
    )


@router.post("/", response_model=schemas.TransactionResponse)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    data = transaction.dict()
    user_category = data.pop("category", None)
    user_subcategory = data.pop("subcategory", None)
    data["amount"] = signed_amount(data.get("amount", 0), data.get("transaction_type", "expense"))

    category, subcategory, confidence, ai_categorized = _resolve_category(
        db,
        current_user.id,
        data.get("description", ""),
        data.get("amount", 0),
        data.get("transaction_type", "expense"),
        data.get("merchant"),
        user_category,
        user_subcategory,
    )

    db_transaction = models.Transaction(
        **data,
        category=category,
        subcategory=subcategory,
        ai_categorized=ai_categorized,
        confidence_score=confidence,
        user_id=current_user.id,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    _refresh_goals(db, current_user.id)
    return db_transaction


@router.get("/", response_model=List[schemas.TransactionResponse])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)

    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)

    return query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()


@router.post("/batch", response_model=List[schemas.TransactionResponse])
async def create_transactions_batch(
    transactions: List[schemas.TransactionCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_transactions = []
    transaction_dicts = [t.dict() for t in transactions]
    categorized = categorizer.batch_categorize(transaction_dicts)

    for txn_data in categorized:
        txn_data["amount"] = signed_amount(
            txn_data.get("amount", 0),
            txn_data.get("transaction_type", "expense"),
        )
        db_transaction = models.Transaction(
            **{
                k: v for k, v in txn_data.items()
                if k not in ("category", "subcategory", "confidence_score", "ai_categorized")
            },
            category=txn_data.get("category"),
            subcategory=txn_data.get("subcategory"),
            ai_categorized=txn_data.get("ai_categorized", True),
            confidence_score=txn_data.get("confidence_score"),
            user_id=current_user.id,
        )
        db.add(db_transaction)
        db_transactions.append(db_transaction)

    db.commit()
    for txn in db_transactions:
        db.refresh(txn)
    _refresh_goals(db, current_user.id)
    return db_transactions


@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.patch("/{transaction_id}/category", response_model=schemas.TransactionResponse)
async def assign_category(
    transaction_id: int,
    payload: schemas.TransactionCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    allowed = set(categorizer.get_available_categories())
    if payload.category not in allowed:
        raise HTTPException(status_code=400, detail="Unknown category")

    db_transaction.category = payload.category
    db_transaction.subcategory = payload.subcategory
    db_transaction.ai_categorized = False
    db_transaction.confidence_score = 1.0
    db.commit()
    db.refresh(db_transaction)
    _refresh_goals(db, current_user.id)
    return db_transaction


@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updates = transaction.dict(exclude_unset=True)
    user_category = updates.pop("category", None)
    user_subcategory = updates.pop("subcategory", None)

    for key, value in updates.items():
        setattr(db_transaction, key, value)

    txn_type = db_transaction.transaction_type or "expense"
    if "amount" in updates or "transaction_type" in updates:
        db_transaction.amount = signed_amount(db_transaction.amount, txn_type)

    if user_category:
        db_transaction.category = user_category
        db_transaction.subcategory = user_subcategory
        db_transaction.ai_categorized = False
        db_transaction.confidence_score = 1.0
    elif "description" in updates and db_transaction.ai_categorized:
        category, subcategory, confidence = categorizer.categorize(
            db_transaction.description,
            db_transaction.amount,
            txn_type,
        )
        db_transaction.category = category
        db_transaction.subcategory = subcategory
        db_transaction.confidence_score = confidence

    db.commit()
    db.refresh(db_transaction)
    _refresh_goals(db, current_user.id)
    return db_transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    _refresh_goals(db, current_user.id)
    return {"message": "Transaction deleted"}
