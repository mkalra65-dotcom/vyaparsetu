from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import ServiceType


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mobile: str = Field(min_length=6, max_length=20)
    email: EmailStr | None = None
    service_interest: ServiceType
    message: str | None = None


class LeadUpdate(BaseModel):
    status: LeadStatus


class LeadRead(BaseModel):
    id: int
    name: str
    mobile: str
    email: str | None
    service_interest: ServiceType
    message: str | None
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
