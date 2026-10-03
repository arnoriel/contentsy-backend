from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.register_user(db, payload.email, payload.password)
    except auth_service.EmailAlreadyRegistered:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token, expires_in = auth_service.authenticate_user(db, payload.email, payload.password)
    except auth_service.InvalidCredentials:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except auth_service.AccountDisabled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled") from None
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
