from sqlalchemy.orm import Session
from app import models
from datetime import datetime
from typing import List
from app.ai.goal_matcher import GoalMatcher

class GoalTracker:
    """Service to automatically track goal progress based on transactions using NLP matching."""
    
    def __init__(self):
        self.goal_matcher = GoalMatcher()
    
    def calculate_goal_progress(self, goal: models.Goal, transactions: List[models.Transaction]) -> float:
        """
        Calculate progress toward a goal based on transactions using NLP to match relevant transactions.
        """
        if not transactions:
            print(f"  No transactions found for user")
            return 0.0
        
        # Use ALL transactions (not just those after goal creation)
        # This makes it easier to track goals - you can create a goal and it will count existing transactions
        relevant_transactions = list(transactions)  # Simply use all transactions
        
        print(f"  Total transactions available: {len(transactions)}")
        
        # Use NLP to match transactions to this specific goal
        total = 0.0
        matched_count = 0
        
        print(f"\n  Calculating progress for goal: '{goal.name}' (type: {goal.goal_type})")
        print(f"  Goal keywords: {self.goal_matcher.extract_keywords_from_goal(goal)}")
        print(f"  Checking {len(relevant_transactions)} transactions...")
        
        for t in relevant_transactions:
            # Check if transaction is relevant to this goal using NLP
            score = self.goal_matcher.calculate_relevance_score(t, goal)
            
            # Show all transactions being checked for debugging
            if score > 0:
                print(f"    Checking: '{t.description}' → score: {score:.2f}")
            
            if score < 0.35:  # Reasonable threshold
                continue  # Skip transactions not related to this goal
            
            print(f"    ✓ Matched: '{t.description}' (score: {score:.2f}, type: {t.transaction_type}, amount: ${abs(t.amount):.2f})")
            
            if goal.goal_type == "savings":
                # For savings: ONLY income counts, expenses are ignored
                if t.transaction_type == "income":
                    matched_count += 1
                    contribution = abs(t.amount)  # Count FULL amount if it matches
                    total += contribution
                    print(f"      → Added ${contribution:.2f} to savings goal (total now: ${total:.2f})")
                else:
                    print(f"      → Skipped: expenses don't count toward savings goals")
                    
            elif goal.goal_type == "debt_payoff":
                # For debt payoff: only payments (expenses) count
                if t.transaction_type == "expense":
                    matched_count += 1
                    contribution = abs(t.amount)  # Count FULL amount
                    total += contribution
                    print(f"      → Added ${contribution:.2f} to debt payoff goal (total now: ${total:.2f})")
                else:
                    print(f"      → Skipped: income doesn't count toward debt payoff goals")
                    
            elif goal.goal_type == "investment":
                # For investment: only investment expenses count
                if t.transaction_type == "expense":
                    matched_count += 1
                    contribution = abs(t.amount)  # Count FULL amount
                    total += contribution
                    print(f"      → Added ${contribution:.2f} to investment goal (total now: ${total:.2f})")
                else:
                    print(f"      → Skipped: income doesn't count toward investment goals")
                    
            elif goal.goal_type == "purchase":
                # For purchase: income adds
                if t.transaction_type == "income":
                    matched_count += 1
                    contribution = abs(t.amount)  # Count FULL amount
                    total += contribution
                    print(f"      → Added ${contribution:.2f} to purchase goal (total now: ${total:.2f})")
                else:
                    print(f"      → Skipped: expenses don't count toward purchase goals")
        
        if matched_count == 0:
            print(f"    ✗ No transactions matched this goal")
        else:
            print(f"    → Final total: ${total:.2f} (matched {matched_count} transactions)")
        
        return max(0.0, total)  # Don't go negative
    
    def update_goal_progress(self, goal: models.Goal, db: Session):
        """Update a single goal's progress based on all transactions using NLP matching."""
        user_id = goal.user_id
        
        # Get all transactions for the user
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id
        ).all()
        
        # Calculate new progress using NLP matching
        new_progress = self.calculate_goal_progress(goal, transactions)
        
        # Update goal
        goal.current_amount = new_progress
        goal.updated_at = datetime.now()
        
        db.commit()
        db.refresh(goal)
        
        return goal
    
    def update_all_goals(self, user_id: int, db: Session):
        """Update progress for all goals of a user using NLP matching."""
        goals = db.query(models.Goal).filter(
            models.Goal.user_id == user_id
        ).all()
        
        if not goals:
            print(f"No goals found for user {user_id}")
            return []
        
        # Get all transactions once
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id
        ).all()
        
        print(f"\n{'='*60}")
        print(f"Updating {len(goals)} goals with {len(transactions)} transactions using NLP matching")
        if len(transactions) > 0:
            print(f"Sample transactions: {[t.description for t in transactions[:3]]}")
        print(f"{'='*60}")
        
        updated_goals = []
        for goal in goals:
            old_progress = goal.current_amount
            new_progress = self.calculate_goal_progress(goal, transactions)
            goal.current_amount = new_progress
            goal.updated_at = datetime.now()
            updated_goals.append(goal)
            if abs(old_progress - new_progress) > 0.01:  # Only log if changed significantly
                print(f"\n✓ Goal '{goal.name}': ${old_progress:.2f} → ${new_progress:.2f}")
        
        db.commit()
        
        for goal in updated_goals:
            db.refresh(goal)
        
        print(f"\n{'='*60}\n")
        
        return updated_goals
