from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("")
def read_pricing() -> dict[str, dict[str, str]]:
    return {
        "gst_registration": {
            "label": "GST Registration",
            "price": settings.PRICING_GST,
        },
        "fssai_registration": {
            "label": "FSSAI Registration",
            "price": settings.PRICING_FSSAI,
        },
        "udyam_registration": {
            "label": "Udyam Registration",
            "price": settings.PRICING_UDYAM,
        },
    }
