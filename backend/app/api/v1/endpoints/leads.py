from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadRead

router = APIRouter()


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: LeadCreate, db: DbSession) -> Lead:
    lead = Lead(
        name=lead_in.name,
        mobile=lead_in.mobile,
        email=lead_in.email,
        service_interest=lead_in.service_interest.value,
        message=lead_in.message,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
