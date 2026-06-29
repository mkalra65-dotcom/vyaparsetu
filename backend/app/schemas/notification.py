from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: int
    user_id: int | None
    application_id: int | None
    channel: str
    event_type: str
    recipient: str
    subject: str
    message: str
    status: str
    provider: str
    provider_message_id: str | None
    error_message: str | None
    is_read: bool
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
