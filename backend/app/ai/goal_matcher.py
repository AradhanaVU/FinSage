from typing import List, Dict, Optional
import re
from app import models

class GoalMatcher:
    """Use NLP to match transactions to goals based on descriptions."""
    
    def __init__(self):
        pass
    
    def extract_keywords_from_goal(self, goal: models.Goal) -> Dict[str, float]:
        """
        Extract keywords from goal name with weights.
        Returns dict of {keyword: weight} where higher weight = more important/specific.
        """
        keywords = {}  # keyword -> weight
        
        goal_name_lower = goal.name.lower()
        words = re.findall(r'\b\w+\b', goal_name_lower)
        
        # Stop words to ignore
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "my", "our", "is", "are", "was", "were"}
        
        # Generic finance words that are too broad (low weight)
        generic_words = {"savings", "save", "fund", "goal", "money", "deposit"}
        
        for word in words:
            if word in stop_words or len(word) <= 2:
                continue
            
            # Generic words get low weight
            if word in generic_words:
                keywords[word] = 0.3
            else:
                # Specific words get high weight
                keywords[word] = 1.0
        
        # Add highly specific terms with extra weight
        if "hawaii" in goal_name_lower:
            keywords["hawaii"] = 2.0  # Very specific location
        if "emergency" in goal_name_lower:
            keywords["emergency"] = 2.0  # Very specific type
            keywords["emergencies"] = 2.0
        if "vacation" in goal_name_lower or "trip" in goal_name_lower:
            keywords["vacation"] = 1.5  # Specific enough
            keywords["trip"] = 1.5
        
        return keywords
    
    def calculate_relevance_score(self, transaction: models.Transaction, goal: models.Goal) -> float:
        """
        Calculate relevance score using weighted keyword matching.
        Returns score between 0.0 (no relevance) and 1.0 (high relevance).
        
        Strategy: Specific keywords (hawaii, emergency) must match for high scores.
        Generic keywords (savings, fund) alone give low scores.
        """
        goal_keywords = self.extract_keywords_from_goal(goal)
        description_lower = transaction.description.lower()
        
        if not goal_keywords:
            return 0.0
        
        # Calculate weighted match score
        total_weight = sum(goal_keywords.values())
        matched_weight = 0.0
        
        for keyword, weight in goal_keywords.items():
            if keyword in description_lower:
                matched_weight += weight
        
        if matched_weight == 0:
            return 0.0
        
        # Score = matched weight / total weight
        # This means you need to match high-weight keywords to get a high score
        base_score = matched_weight / total_weight
        
        # Apply transaction type filter for goal type
        if goal.goal_type == "savings":
            # Only income counts toward savings goals
            if transaction.transaction_type == "income":
                return min(1.0, base_score * 1.2)
            else:
                return 0.0  # Expenses don't help savings
                
        elif goal.goal_type == "debt_payoff":
            # Only expenses (payments) count
            if transaction.transaction_type == "expense":
                return min(1.0, base_score * 1.2)
            else:
                return 0.0
                
        elif goal.goal_type == "investment":
            # Only investment expenses count
            if transaction.transaction_type == "expense":
                return min(1.0, base_score)
            else:
                return 0.0
            
        elif goal.goal_type == "purchase":
            # Income counts positive
            if transaction.transaction_type == "income":
                return min(1.0, base_score * 1.2)
            else:
                return 0.0
        
        return min(1.0, base_score)
    
    def should_count_toward_goal(self, transaction: models.Transaction, goal: models.Goal, threshold: float = 0.5) -> bool:
        """Determine if a transaction should count toward a goal."""
        score = self.calculate_relevance_score(transaction, goal)
        return score >= threshold
    
    def match_transactions_to_goal(self, transactions: List[models.Transaction], goal: models.Goal) -> List[Dict]:
        """Match transactions to a goal and return relevant ones with scores."""
        matches = []
        for txn in transactions:
            score = self.calculate_relevance_score(txn, goal)
            if score > 0:
                matches.append({
                    "transaction": txn,
                    "score": score,
                    "should_count": self.should_count_toward_goal(txn, goal)
                })
        return sorted(matches, key=lambda x: x["score"], reverse=True)
