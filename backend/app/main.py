from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import hash_password
from app.database import engine, Base, SessionLocal
from app import models
from app.routers import (
    auth, transactions, goals, ai_insights, chat,
    alerts, simulations, receipts, risk_analysis
)
import secrets

if not settings.is_production:
    Base.metadata.create_all(bind=engine)


def _reserve_legacy_demo_tenant():
    """
    Existing SQLite demos used hardcoded user_id=1 without a users row.
    Reserve that tenant so the first real signup does not inherit it.
    """
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return
        has_orphan = (
            db.query(models.Transaction).filter(models.Transaction.user_id == 1).first()
            or db.query(models.Goal).filter(models.Goal.user_id == 1).first()
        )
        if not has_orphan:
            return
        db.add(
            models.User(
                email="legacy-demo@local.invalid",
                username="legacy-demo",
                hashed_password=hash_password(secrets.token_urlsafe(48)),
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Legacy tenant reserve skipped: {exc}")
    finally:
        db.close()


_reserve_legacy_demo_tenant()

app = FastAPI(
    title="FinSage - AI Finance Companion",
    description="An intelligent financial assistant with AI-powered insights, risk analysis, and personalized recommendations",
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
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
    return {"status": "healthy", "env": settings.ENV}
