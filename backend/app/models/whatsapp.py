from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class WhatsAppContact(Base):
    __tablename__ = "whatsapp_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    wa_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    consent_status: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
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

    user = relationship("User")
    sessions = relationship("ConversationSession", back_populates="contact")
    messages = relationship("ConversationMessage", back_populates="contact")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    state: Mapped[str] = mapped_column(String(100), default="awaiting_service_selection", nullable=False)
    selected_service_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    contact = relationship("WhatsAppContact", back_populates="sessions")
    application = relationship("Application")
    messages = relationship("ConversationMessage", back_populates="session")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="whatsapp", nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    contact = relationship("WhatsAppContact", back_populates="messages")
    session = relationship("ConversationSession", back_populates="messages")
    application = relationship("Application")
