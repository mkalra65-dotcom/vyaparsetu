from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationAuditLogRead(BaseModel):
    id: int
    application_id: int
    actor_user_id: int
    action: str
    old_status: str | None
    new_status: str | None
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
