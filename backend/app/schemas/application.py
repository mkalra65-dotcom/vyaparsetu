from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApplicationStatus, ServiceType


class ApplicationBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    service_type: ServiceType
    business_name: str = Field(min_length=1, max_length=255)
    proprietor_name: str | None = Field(default=None, max_length=255)
    applicant_mobile: str | None = Field(default=None, max_length=20)
    applicant_email: str | None = Field(default=None, max_length=255)
    pan_number: str | None = Field(default=None, max_length=20)
    aadhaar_number: str | None = Field(default=None, max_length=20)
    business_address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    state: str | None = Field(default=None, max_length=100)
    business_type: str | None = Field(default=None, max_length=100)
    business_constitution: str | None = Field(default=None, max_length=100)
    nature_of_business: str | None = Field(default=None, max_length=255)
    principal_place_of_business: str | None = None
    bank_account_details: str | None = None
    expected_turnover: str | None = Field(default=None, max_length=100)
    annual_turnover: str | None = Field(default=None, max_length=100)
    food_business_type: str | None = Field(default=None, max_length=100)
    food_category: str | None = Field(default=None, max_length=100)
    premises_address: str | None = None
    license_type_suggestion: str | None = Field(default=None, max_length=100)
    fssai_license_category: str | None = Field(default=None, max_length=100)
    enterprise_name: str | None = Field(default=None, max_length=255)
    type_of_organisation: str | None = Field(default=None, max_length=100)
    major_activity: str | None = Field(default=None, max_length=100)
    nic_code: str | None = Field(default=None, max_length=50)
    enterprise_type: str | None = Field(default=None, max_length=100)
    investment_amount: str | None = Field(default=None, max_length=100)
    turnover: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_service_fields(self) -> Self:
        required_fields_by_service = {
            ServiceType.GST_REGISTRATION: [
                "pan_number",
                "business_address",
                "state",
                "business_constitution",
            ],
            ServiceType.FSSAI_REGISTRATION: [
                "business_address",
                "food_business_type",
                "fssai_license_category",
            ],
            ServiceType.UDYAM_REGISTRATION: [
                "pan_number",
                "enterprise_type",
            ],
        }
        missing_fields = [
            field_name
            for field_name in required_fields_by_service[self.service_type]
            if not getattr(self, field_name)
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for {self.service_type.value}: "
                f"{', '.join(missing_fields)}"
            )
        return self


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ApplicationStatus | None = None
    business_name: str | None = Field(default=None, min_length=1, max_length=255)
    proprietor_name: str | None = Field(default=None, max_length=255)
    applicant_mobile: str | None = Field(default=None, max_length=20)
    applicant_email: str | None = Field(default=None, max_length=255)
    pan_number: str | None = Field(default=None, max_length=20)
    aadhaar_number: str | None = Field(default=None, max_length=20)
    business_address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    state: str | None = Field(default=None, max_length=100)
    business_type: str | None = Field(default=None, max_length=100)
    business_constitution: str | None = Field(default=None, max_length=100)
    nature_of_business: str | None = Field(default=None, max_length=255)
    principal_place_of_business: str | None = None
    bank_account_details: str | None = None
    expected_turnover: str | None = Field(default=None, max_length=100)
    annual_turnover: str | None = Field(default=None, max_length=100)
    food_business_type: str | None = Field(default=None, max_length=100)
    food_category: str | None = Field(default=None, max_length=100)
    premises_address: str | None = None
    license_type_suggestion: str | None = Field(default=None, max_length=100)
    fssai_license_category: str | None = Field(default=None, max_length=100)
    enterprise_name: str | None = Field(default=None, max_length=255)
    type_of_organisation: str | None = Field(default=None, max_length=100)
    major_activity: str | None = Field(default=None, max_length=100)
    nic_code: str | None = Field(default=None, max_length=50)
    enterprise_type: str | None = Field(default=None, max_length=100)
    investment_amount: str | None = Field(default=None, max_length=100)
    turnover: str | None = Field(default=None, max_length=100)
    customer_clarification_message: str | None = None
    internal_admin_notes: str | None = None


class ApplicationRead(BaseModel):
    id: int
    title: str
    description: str | None
    service_type: ServiceType
    status: ApplicationStatus
    business_name: str
    proprietor_name: str | None
    applicant_mobile: str | None
    applicant_email: str | None
    pan_number: str | None
    aadhaar_number: str | None
    business_address: str | None
    city: str | None
    pincode: str | None
    state: str | None
    business_type: str | None
    business_constitution: str | None
    nature_of_business: str | None
    principal_place_of_business: str | None
    bank_account_details: str | None
    expected_turnover: str | None
    annual_turnover: str | None
    food_business_type: str | None
    food_category: str | None
    premises_address: str | None
    license_type_suggestion: str | None
    fssai_license_category: str | None
    enterprise_name: str | None
    type_of_organisation: str | None
    major_activity: str | None
    nic_code: str | None
    enterprise_type: str | None
    investment_amount: str | None
    turnover: str | None
    customer_clarification_message: str | None
    internal_admin_notes: str | None = None
    health_score: int | None = None
    ai_review_summary: str | None = None
    required_documents: list[str]
    missing_required_documents: list[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
