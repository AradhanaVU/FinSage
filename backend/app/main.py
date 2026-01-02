from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    transactions, goals, ai_insights, chat, 
    alerts, simulations, receipts, risk_analysis
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinSage - AI Finance Companion",
    description="An intelligent financial assistant with AI-powered insights, risk analysis, and personalized recommendations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
app.include_router(ai_insights.router, prefix="/api/ai", tags=["ai-insights"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(simulations.router, prefix="/api/simulations", tags=["simulations"])
app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
app.include_router(risk_analysis.router, prefix="/api/risk", tags=["risk-analysis"])

@app.get("/")
async def root():
    return {"message": "FinSage API - AI Finance Companion"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


