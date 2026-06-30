from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class CustomerFeedback(Base):
    __tablename__ = "customer_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    application = relationship("Application", back_populates="feedback_entries")
    user = relationship("User")
