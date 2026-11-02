import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.models import WebhookEvent, Message
from app.schemas import WebhookPayload
from app.customer_service import receive_customer_message
from app.ai.draft_service import generate_draft_for_message


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


# ==========================================
# SIGNATURE VERIFICATION
# ==========================================

def verify_signature(
    raw_body: bytes,
    signature: str | None,
) -> bool:

    if not signature or not signature.startswith("sha256="):
        return False

    supplied_digest = signature.removeprefix("sha256=")

    if len(supplied_digest) != 64:
        return False

    expected_digest = hmac.new(
        settings.webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_digest,
        supplied_digest,
    )


# ==========================================
# DUPLICATE EVENT HANDLING
# ==========================================

def handle_duplicate_event(db: Session, existing: WebhookEvent):

    # Find the original message associated with this event
    message = db.scalar(
        select(Message).where(
            Message.external_message_id == existing.message_id
        )
    )

    ai_draft_status = None

    if message:
        # Generate or retry the draft for the original message
        draft = generate_draft_for_message(
            db=db,
            conversation_id=message.conversation_id,
            message_id=message.id,
        )

        ai_draft_status = draft.status

    return {
        "status": "ok",
        "event_id": existing.event_id,
        "duplicate": True,
        "ai_draft_status": ai_draft_status,
    }


# ==========================================
# RECEIVE WEBHOOK
# ==========================================

@router.post("/messages")
async def receive_message(
    request: Request,
    db: Session = Depends(get_db),
):

    # 1. Read raw request body
    raw_body = await request.body()

    # 2. Verify HMAC signature
    signature = request.headers.get("X-Signature")

    if not verify_signature(raw_body, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    # 3. Validate payload
    try:
        payload = WebhookPayload.model_validate_json(raw_body)

    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Invalid webhook payload",
        )

    # 4. Check duplicate event
    existing = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.event_id == payload.event_id
        )
    )

    if existing:
        return handle_duplicate_event(db, existing)

    try:

        # 5. Save event
        event = WebhookEvent(
            event_id=payload.event_id,
            event_type=payload.type,
            brand_id=payload.brand_id,
            customer_id=payload.customer.id,
            customer_name=payload.customer.name,
            customer_phone=payload.customer.phone,
            message_id=payload.message.id,
            message_text=payload.message.text,
            event_timestamp=payload.timestamp,
            payload=json.loads(raw_body),
            status="received",
        )

        db.add(event)
        db.flush()

        # 6. Save customer, conversation and message
        conversation, message, duplicate_message = (
            receive_customer_message(
                db,
                customer_id=payload.customer.id,
                brand_id=payload.brand_id,
                name=payload.customer.name,
                phone=payload.customer.phone,
                text=payload.message.text,
                external_message_id=payload.message.id,
                message_timestamp=payload.timestamp,
            )
        )

        # 7. Mark event processed
        event.status = "processed"

        # 8. Commit everything together
        db.commit()

        # 9. Generate AI draft after customer message is safely saved
        draft = generate_draft_for_message(
            db=db,
            conversation_id=conversation.id,
            message_id=message.id,
        )

        return {
            "status": "ok",
            "event_id": event.event_id,
            "conversation_id": str(conversation.id),
            "message_id": str(message.id),
            "duplicate": False,
            "ai_draft_status": draft.status,
        }

    except IntegrityError:

        db.rollback()

        # Handle simultaneous delivery of the same event
        existing = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == payload.event_id
            )
        )

        if existing:
            return handle_duplicate_event(db, existing)

        raise HTTPException(
            status_code=409,
            detail="Database uniqueness conflict",
        )

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not process webhook",
        )