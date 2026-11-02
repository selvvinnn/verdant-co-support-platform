
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Conversation, Message
from app.customer_service import receive_customer_message
from app.schemas import CustomerMessageCreate
from app.ai.draft_service import generate_draft_for_message

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import create_customer_access_token
import jwt

from app.database import settings
from app.auth import ALGORITHM

import logging

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/customer",
    tags=["Customer"],
)

customer_security = HTTPBearer(auto_error=False)


# =====================================
# SEND CUSTOMER MESSAGE
# =====================================

@router.post("/messages", status_code=201)
def send_customer_message(
    request: CustomerMessageCreate,
    db: Session = Depends(get_db),
):
    # STEP 1: Save the customer message
    try:
        conversation, message, duplicate = receive_customer_message(
            db,
            customer_id=request.customer_id,
            brand_id=request.brand_id,
            name=request.name,
            phone=request.phone,
            text=request.text,
        )

        db.commit()
        db.refresh(message)
        db.refresh(conversation)

    except (KeyError, TypeError):
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Invalid customer message",
        )

    except Exception:
        db.rollback()
        logger.exception("Could not save customer message")

        raise HTTPException(
            status_code=500,
            detail="Could not save customer message",
        )

    # STEP 2: Generate customer access token
    customer_token = create_customer_access_token(
        conversation_id=conversation.id,
        customer_id=conversation.customer_id,
    )

    # STEP 3: Generate AI draft independently
    draft_status = "failed"

    try:
        draft = generate_draft_for_message(
            db=db,
            conversation_id=conversation.id,
            message_id=message.id,
        )

        draft_status = draft.status

    except Exception:
        logger.exception(
            "AI draft processing failed for message %s",
            message.id,
        )

        # The customer message was already committed.
        # Do not roll it back because AI generation failed.
        draft_status = "failed"

    # STEP 4: Return successful customer message response
    return {
        "status": "ok",
        "conversation_id": str(conversation.id),
        "message_id": str(message.id),
        "duplicate": duplicate,
        "ai_draft_status": draft_status,
        "customer_access_token": customer_token,
    }


# =====================================
# GET CUSTOMER CONVERSATION
# =====================================

@router.get("/conversations/{conversation_id}")
def get_customer_conversation(
    conversation_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        customer_security
    ),
    db: Session = Depends(get_db),
):

    # 1. Require a customer access token
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Customer authentication required",
        )

    # 2. Verify token signature and expiry
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
        )

        if payload.get("token_type") != "customer":
            raise HTTPException(
                status_code=401,
                detail="Invalid customer token",
            )

        token_conversation_id = UUID(payload["conversation_id"])
        token_customer_id = UUID(payload["sub"])

    except HTTPException:
        raise

    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired customer token",
        )

    # 3. Ensure token belongs to the requested conversation
    if token_conversation_id != conversation_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access this conversation",
        )

    # 4. Retrieve conversation
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # 5. Verify customer ownership
    if conversation.customer_id != token_customer_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access this conversation",
        )

    customer = db.get(Customer, conversation.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # 6. Retrieve only customer and agent messages
    messages = db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.sender_type.in_(["customer", "agent"]),
        )
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
    ).all()

    return {
        "conversation_id": str(conversation.id),
        "customer": {
            "id": customer.external_customer_id,
            "name": customer.name,
            "phone": customer.phone,
        },
        "status": conversation.status,
        "messages": [
            {
                "message_id": str(message.id),
                "sender_type": message.sender_type,
                "text": message.text,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }