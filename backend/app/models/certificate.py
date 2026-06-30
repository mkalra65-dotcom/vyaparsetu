from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    certificate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application = relationship("Application", back_populates="certificates")
    uploaded_by_user = relationship("User")
