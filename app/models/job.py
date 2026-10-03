import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import JobStatus, enum_values
from app.models.user import User

if TYPE_CHECKING:
    from app.models.clip import Clip


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("clip_count BETWEEN 1 AND 5", name="clip_count_range"),
        Index("ix_jobs_user_id_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value,
        index=True,
        nullable=False,
    )
    clip_count: Mapped[int] = mapped_column(Integer, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="jobs")
    clips: Mapped[list["Clip"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="Clip.position"
    )
