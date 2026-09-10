from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.goal_tracker import GoalTracker
from app.deps import get_current_user

router = APIRouter()
goal_tracker = GoalTracker()


@router.post("/", response_model=schemas.GoalResponse)
async def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_goal = models.Goal(
        **goal.dict(),
        user_id=current_user.id,
        current_amount=0.0,
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.get("/", response_model=List[schemas.GoalResponse])
async def get_goals(
    recalculate: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if recalculate:
        goal_tracker.update_all_goals(current_user.id, db)

    return (
        db.query(models.Goal)
        .filter(models.Goal.user_id == current_user.id)
        .order_by(models.Goal.priority.desc(), models.Goal.created_at.desc())
        .all()
    )


@router.get("/{goal_id}", response_model=schemas.GoalResponse)
async def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.put("/{goal_id}", response_model=schemas.GoalResponse)
async def update_goal(
    goal_id: int,
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if recalculate or amount is None:
        goal_tracker.update_goal_progress(db_goal, db)
    else:
        db_goal.current_amount = amount
        db.commit()
        db.refresh(db_goal)
    return db_goal


@router.post("/recalculate-all")
async def recalculate_all_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    updated_goals = goal_tracker.update_all_goals(current_user.id, db)
    return {
        "message": f"Recalculated {len(updated_goals)} goals using NLP matching",
        "goals": updated_goals,
    }


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted"}
