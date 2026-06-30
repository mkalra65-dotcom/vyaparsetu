from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class GovernmentQuery(Base):
    __tablename__ = "government_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raised_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    response_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    required_document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)
    sent_to_customer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overdue_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    application = relationship("Application", back_populates="government_queries")
    raised_by = relationship("User")
    response_document = relationship("Document")
