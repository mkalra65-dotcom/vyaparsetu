import re
from pathlib import Path

from app.services.ai.base import DocumentAIProvider, DocumentExtractionResult

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
AADHAAR_PATTERN = re.compile(r"^[0-9]{12}$")
IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


class MockAIProvider(DocumentAIProvider):
    provider_name = "mock"

    def extract_document_fields(self, file_path: str, document_type: str) -> DocumentExtractionResult:
        filename = Path(file_path).name.lower()
        fields: dict[str, str] = {}
        warnings: list[str] = []

        if document_type == "pan_card":
            fields["pan_number"] = "ABCDE1234F" if "invalid" not in filename else "INVALID"
            if not PAN_PATTERN.match(fields["pan_number"]):
                warnings.append("PAN format could not be validated")
        elif document_type == "aadhaar_card":
            fields["aadhaar_number"] = "123456789012" if "invalid" not in filename else "1234"
            if not AADHAAR_PATTERN.match(fields["aadhaar_number"]):
                warnings.append("Aadhaar pattern could not be validated")
        elif document_type in {"business_address_proof", "food_business_address_proof"}:
            fields["address"] = "123 Market Road, Delhi" if "missing" not in filename else ""
            if not fields["address"]:
                warnings.append("Address was not detected")
        elif document_type == "bank_account_proof":
            fields["account_number"] = "123456789012"
            fields["ifsc"] = "HDFC0123456" if "invalid" not in filename else "BADIFSC"
            if not fields["account_number"]:
                warnings.append("Bank account number was not detected")
            if not IFSC_PATTERN.match(fields["ifsc"]):
                warnings.append("IFSC could not be validated")
        else:
            warnings.append("Document type is not supported for extraction")

        return DocumentExtractionResult(
            document_type=document_type,
            extracted_fields=fields,
            confidence_score=0.95 if not warnings else 0.7,
            validation_warnings=warnings,
        )
