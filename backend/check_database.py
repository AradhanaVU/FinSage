"""Check what's stored in the database"""
from app.database import SessionLocal
from app.models import User, Transaction, Goal, Alert

db = SessionLocal()

print("\n" + "="*60)
print("DATABASE CONTENTS")
print("="*60)

# Counts
print(f"\nUsers: {db.query(User).count()}")
print(f"Transactions: {db.query(Transaction).count()}")
print(f"Goals: {db.query(Goal).count()}")
print(f"Alerts: {db.query(Alert).count()}")

# Recent Transactions
print("\n" + "-"*60)
print("RECENT TRANSACTIONS (Last 5)")
print("-"*60)
for t in db.query(Transaction).order_by(Transaction.date.desc()).limit(5).all():
    amount_str = f"${abs(t.amount):.2f}"
    print(f"{t.date.date()} | {t.description:30s} | {amount_str:>10s} | {t.transaction_type:8s} | {t.category or 'N/A'}")

# All Transactions Summary
print("\n" + "-"*60)
print("ALL TRANSACTIONS")
print("-"*60)
all_txns = db.query(Transaction).order_by(Transaction.date.desc()).all()
for t in all_txns:
    amount_str = f"${abs(t.amount):.2f}"
    print(f"{t.date.date()} | {t.description:30s} | {amount_str:>10s} | {t.transaction_type:8s}")

# Goals
print("\n" + "-"*60)
print("GOALS")
print("-"*60)
for g in db.query(Goal).all():
    progress_pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
    print(f"{g.name:25s} | ${g.current_amount:>8.2f} / ${g.target_amount:>8.2f} ({progress_pct:>5.1f}%) | {g.goal_type}")

# Summary Stats
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
total_income = sum(abs(t.amount) for t in all_txns if t.transaction_type == "income")
total_expenses = sum(abs(t.amount) for t in all_txns if t.transaction_type == "expense")
net = total_income - total_expenses

print(f"Total Income:   ${total_income:>10.2f}")
print(f"Total Expenses: ${total_expenses:>10.2f}")
print(f"Net:            ${net:>10.2f}")
print("="*60 + "\n")

db.close()


