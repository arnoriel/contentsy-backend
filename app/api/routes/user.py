from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import CreditsOut
from app.services.credit_service import get_balance

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/credits", response_model=CreditsOut)
def credits(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return CreditsOut(credits=get_balance(db, user.id))
