from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.credit_service import get_balance

_bearer = HTTPBearer(auto_error=False)  # auto_error=False → kita kontrol sendiri biar 401 (bukan 403)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthorized()
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise _unauthorized("Invalid or expired token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    return user


def require_credit(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Pre-check credit ≥ 1 (dipakai BE-Azriel-04). Pengurangan tetap atomic via deduct_credit."""
    if get_balance(db, user.id) < 1:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient credits")
    return user
