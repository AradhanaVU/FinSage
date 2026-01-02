from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.goal_tracker import GoalTracker

router = APIRouter()
goal_tracker = GoalTracker()  # Create instance

@router.post("/", response_model=schemas.GoalResponse)
async def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    """Create a new financial goal."""
    db_goal = models.Goal(
        **goal.dict(),
        user_id=1,  # TODO: Get from authentication
        current_amount=0.0
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

@router.get("/", response_model=List[schemas.GoalResponse])
async def get_goals(
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """Get all goals for the user. Optionally recalculate progress."""
    user_id = 1  # TODO: Auth
    
    # Optionally recalculate progress before returning
    if recalculate:
        goal_tracker.update_all_goals(user_id, db)
    
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).order_by(models.Goal.priority.desc(), models.Goal.created_at.desc()).all()
    
    return goals

@router.get("/{goal_id}", response_model=schemas.GoalResponse)
async def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get a specific goal."""
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == 1  # TODO: Auth
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal

@router.put("/{goal_id}", response_model=schemas.GoalResponse)
async def update_goal(
    goal_id: int,
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db)
):
    """Update a goal."""
    db_goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == 1  # TODO: Auth
    ).first()
    
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    for key, value in goal.dict().items():
        setattr(db_goal, key, value)
    
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

@router.patch("/{goal_id}/progress", response_model=schemas.GoalResponse)
async def update_goal_progress(
    goal_id: int,
    amount: float = None,
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """Update the current progress of a goal. If recalculate=True, auto-calculate from transactions using NLP."""
    db_goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == 1  # TODO: Auth
    ).first()
    
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    if recalculate:
        # Automatically calculate from transactions using NLP matching
        goal_tracker.update_goal_progress(db_goal, db)
    elif amount is not None:
        # Manually set amount
        db_goal.current_amount = amount
        db.commit()
        db.refresh(db_goal)
    else:
        # Default: recalculate using NLP
        goal_tracker.update_goal_progress(db_goal, db)
    
    return db_goal

@router.post("/recalculate-all")
async def recalculate_all_goals(db: Session = Depends(get_db)):
    """Recalculate progress for all goals based on current transactions using NLP matching."""
    user_id = 1  # TODO: Auth
    updated_goals = goal_tracker.update_all_goals(user_id, db)
    return {
        "message": f"Recalculated {len(updated_goals)} goals using NLP matching",
        "goals": updated_goals
    }

@router.delete("/{goal_id}")
async def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal."""
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == 1  # TODO: Auth
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
    
    return {"message": "Goal deleted"}
