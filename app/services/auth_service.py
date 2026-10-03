from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)
from app.models.credit import Credit
from app.models.user import User


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class AccountDisabled(Exception):
    pass


def register_user(db: Session, email: str, password: str) -> User:
    if db.scalar(select(User.id).where(User.email == email)):
        raise EmailAlreadyRegistered

    user = User(email=email, hashed_password=hash_password(password))
    user.credit = Credit(balance=get_settings().signup_credits)
    db.add(user)
    try:
        db.commit()  # user + credit dalam 1 transaksi
    except IntegrityError:  # race: email sama masuk bersamaan
        db.rollback()
        raise EmailAlreadyRegistered from None
    return user


def authenticate_user(db: Session, email: str, password: str) -> tuple[str, int]:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_dummy_password(password)
        raise InvalidCredentials
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials
    if not user.is_active:
        raise AccountDisabled

    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
        db.commit()

    return create_access_token(user.id)
