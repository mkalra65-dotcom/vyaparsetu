from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ApplicationTimelineEvent(Base):
    __tablename__ = "application_timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_channel: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    application = relationship("Application", back_populates="timeline_events")
    actor = relationship("User")
