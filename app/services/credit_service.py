import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.credit import Credit


def get_balance(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(select(Credit.balance).where(Credit.user_id == user_id)) or 0


def deduct_credit(db: Session, user_id: uuid.UUID, amount: int = 1) -> int | None:
    """Atomic deduct (aman dari race condition). Return saldo baru, atau None kalau saldo kurang.

    Tidak commit — caller (BE-Azriel-04) commit bareng insert job dalam 1 transaksi.
    """
    stmt = (
        update(Credit)
        .where(Credit.user_id == user_id, Credit.balance >= amount)
        .values(balance=Credit.balance - amount)
        .returning(Credit.balance)
    )
    return db.execute(stmt).scalar_one_or_none()
