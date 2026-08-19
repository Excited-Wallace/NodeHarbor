from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, TokenResponse, UserInfo
from app.database import get_db
from app.services.auth_service import authenticate
from app.auth import create_access_token
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return TokenResponse(access_token=access_token, role=user.role)

@router.get("/me", response_model=UserInfo)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserInfo(username=current_user.username, role=current_user.role)
