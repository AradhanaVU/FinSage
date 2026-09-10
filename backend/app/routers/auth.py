from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import hash_password, verify_password, create_access_token
from app.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    username = payload.username.strip()
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    existing = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    user = models.User(
        email=email,
        username=username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password form: username field accepts email or username."""
    identifier = form_data.username.strip()
    user = db.query(models.User).filter(
        (models.User.email == identifier.lower()) | (models.User.username == identifier)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.post("/login/json", response_model=schemas.TokenResponse)
def login_json(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    identifier = payload.username.strip()
    user = db.query(models.User).filter(
        (models.User.email == identifier.lower()) | (models.User.username == identifier)
    ).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )
    token = create_access_token(user.id)
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
