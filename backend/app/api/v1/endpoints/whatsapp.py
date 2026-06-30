from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.api.deps import DbSession
from app.core.config import settings
from app.services.whatsapp.conversation import (
    MENU_MESSAGE,
    get_or_create_contact,
    get_or_create_session,
    handle_media_message,
    handle_text_message,
    send_and_store_message,
    store_message,
)

router = APIRouter()


@router.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> str:
    if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN and challenge:
        return challenge
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid WhatsApp webhook verification")


def _iter_whatsapp_messages(payload: dict) -> list[tuple[dict, dict]]:
    messages: list[tuple[dict, dict]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            contacts = value.get("contacts") or []
            contact_by_wa_id = {
                contact.get("wa_id"): contact
                for contact in contacts
                if contact.get("wa_id")
            }
            for message in value.get("messages", []):
                contact = contact_by_wa_id.get(message.get("from"), {})
                messages.append((message, contact))
    return messages


@router.post("/webhook")
async def receive_webhook(request: Request, db: DbSession) -> dict[str, int | str]:
    payload = await request.json()
    processed_messages = 0

    for message, contact_payload in _iter_whatsapp_messages(payload):
        phone_number = message.get("from")
        if not phone_number:
            continue

        message_type = message.get("type") or "unknown"
        provider_message_id = message.get("id")
        wa_id = contact_payload.get("wa_id") or phone_number
        display_name = (contact_payload.get("profile") or {}).get("name")

        if message_type == "text":
            body = (message.get("text") or {}).get("body") or ""
            handle_text_message(
                db,
                phone_number=phone_number,
                wa_id=wa_id,
                display_name=display_name,
                provider_message_id=provider_message_id,
                message_body=body,
                raw_payload=message,
            )
        elif message_type in {"document", "image"}:
            handle_media_message(
                db,
                phone_number=phone_number,
                wa_id=wa_id,
                display_name=display_name,
                provider_message_id=provider_message_id,
                message_type=message_type,
                media_payload=message.get(message_type) or {},
                raw_payload=message,
            )
        else:
            contact = get_or_create_contact(
                db,
                phone_number=phone_number,
                wa_id=wa_id,
                display_name=display_name,
            )
            session = get_or_create_session(db, contact)
            store_message(
                db,
                contact=contact,
                session=session,
                direction="inbound",
                message_type=message_type,
                body=None,
                provider_message_id=provider_message_id,
                raw_payload=message,
            )
            send_and_store_message(
                db,
                contact=contact,
                session=session,
                message=(
                    "I can start your registration over text right now. "
                    f"{MENU_MESSAGE}"
                ),
            )

        processed_messages += 1

    db.commit()
    return {"status": "received", "processed_messages": processed_messages}
