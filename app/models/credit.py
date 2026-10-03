import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User


class Credit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "credits"
    __table_args__ = (CheckConstraint("balance >= 0", name="balance_non_negative"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)

    user: Mapped[User] = relationship(back_populates="credit")
