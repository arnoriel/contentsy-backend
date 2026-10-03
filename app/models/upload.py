import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User


class Upload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """`id` = upload_id yang dikembalikan ke FE dan dipakai di POST /api/jobs."""

    __tablename__ = "uploads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(100), nullable=False)  # relatif ke UPLOAD_DIR
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user: Mapped[User] = relationship(back_populates="uploads")
