from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.ai.llm_chat import FinancialCoachChat
from collections import defaultdict

router = APIRouter()
chat_ai = FinancialCoachChat()

@router.get("/status")
async def chat_status():
    """Check which AI provider is being used."""
    return {
        "provider": chat_ai.provider if chat_ai.provider else "fallback",
        "has_client": chat_ai.client is not None,
        "message": f"Using {chat_ai.provider} API" if chat_ai.provider else "No AI API configured - using fallback responses"
    }

@router.post("/", response_model=schemas.ChatResponse)
async def chat(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db)
):
    """Chat with the financial coach AI."""
    # Build context from user's financial data
    user_id = 1  # TODO: Get from authentication
    
    # Get recent transactions
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= datetime.now() - timedelta(days=90)
    ).all()
    
    # Get goals
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).all()
    
    # Calculate financial context
    context = {}
    
    # Calculate monthly income and expenses
    monthly_income = sum(
        t.amount for t in transactions
        if t.transaction_type == "income" and
        t.date >= datetime.now() - timedelta(days=30)
    )
    
    monthly_expenses = sum(
        abs(t.amount) for t in transactions
        if t.transaction_type == "expense" and
        t.date >= datetime.now() - timedelta(days=30)
    )
    
    # Calculate current balance (simplified)
    current_balance = sum(
        t.amount if t.transaction_type == "income" else -abs(t.amount)
        for t in transactions
    )
    
    # Top spending categories
    category_totals = defaultdict(float)
    for txn in transactions:
        if txn.transaction_type == "expense" and txn.category:
            category_totals[txn.category] += abs(txn.amount)
    
    top_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    context = {
        "current_balance": current_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "goals": [
            {
                "id": g.id,
                "name": g.name,
                "current_amount": g.current_amount,
                "target_amount": g.target_amount
            }
            for g in goals
        ],
        "top_categories": [cat for cat, _ in top_categories]
    }
    
    # Get AI response
    response = chat_ai.chat(message.message, context)
    
    return response

