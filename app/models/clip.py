import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AspectRatio, enum_values
from app.models.job import Job


class Clip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clips"
    __table_args__ = (
        UniqueConstraint("job_id", "position", name="job_position"),
        CheckConstraint("end_time > start_time", name="time_range"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[AspectRatio] = mapped_column(
        Enum(
            AspectRatio,
            name="aspect_ratio",
            native_enum=False,
            length=8,
            create_constraint=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    subtitle_style: Mapped[str] = mapped_column(String(50), nullable=False)
    grid_enabled: Mapped[bool] = mapped_column(Boolean, server_default=false(), nullable=False)
    start_time: Mapped[float | None] = mapped_column(Float)
    end_time: Mapped[float | None] = mapped_column(Float)
    duration: Mapped[float | None] = mapped_column(Float)
    video_path: Mapped[str | None] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    job: Mapped[Job] = relationship(back_populates="clips")
