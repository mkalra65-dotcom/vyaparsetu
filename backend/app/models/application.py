from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ApplicationStatus, ServiceType


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ApplicationStatus.DRAFT.value,
        nullable=False,
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    proprietor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applicant_mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    applicant_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pan_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    aadhaar_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    business_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_constitution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nature_of_business: Mapped[str | None] = mapped_column(String(255), nullable=True)
    principal_place_of_business: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_account_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_turnover: Mapped[str | None] = mapped_column(String(100), nullable=True)
    annual_turnover: Mapped[str | None] = mapped_column(String(100), nullable=True)
    food_business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    food_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    premises_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_type_suggestion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fssai_license_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enterprise_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type_of_organisation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    major_activity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nic_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enterprise_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    investment_amount: Mapped[str | None] = mapped_column(String(100), nullable=True)
    turnover: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_clarification_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_score: Mapped[int | None] = mapped_column(default=None, nullable=True)
    ai_review_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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

    owner = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    audit_logs = relationship(
        "ApplicationAuditLog",
        back_populates="application",
        cascade="all, delete-orphan",
    )
