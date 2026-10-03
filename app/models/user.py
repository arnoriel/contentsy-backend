from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.job import Job
    from app.models.upload import Upload


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=False)

    credit: Mapped["Credit | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )
    uploads: Mapped[list["Upload"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def credits(self) -> int:
        return self.credit.balance if self.credit else 0
