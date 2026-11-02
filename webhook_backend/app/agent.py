from uuid import UUID

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import (
    Agent,
    Customer,
    Conversation,
    Message,
    ReplyDraft,
)
from app.auth import get_current_agent



router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"],
)

class DraftUpdateRequest(BaseModel):
    draft_text: str = Field(min_length=1, max_length=5000)

# =====================================
# GET LOGGED-IN AGENT
# =====================================

@router.get("/me")
def get_agent_profile(
    current_agent: Agent = Depends(get_current_agent),
):
    return {
        "id": str(current_agent.id),
        "email": current_agent.email,
    }


# =====================================
# LIST ALL CONVERSATIONS
# =====================================

@router.get("/conversations")
def list_conversations( 
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    # Subquery: latest message text for each conversation
    latest_message = (
        select(Message.text)
        .where(Message.conversation_id == Conversation.id)
        .order_by(
            Message.created_at.desc(),
            Message.id.desc(),
        )
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )

    conversations = db.execute(
        select(
            Conversation,
            Customer,
            latest_message.label("latest_message"),
        )
        .join(
            Customer,
            Customer.id == Conversation.customer_id,
        )
        .order_by(Conversation.updated_at.desc())
    ).all()

    results = []

    for conversation, customer, message_text in conversations:

        results.append({
            "conversation_id": str(conversation.id),
            "customer": {
                "id": customer.external_customer_id,
                "name": customer.name,
                "phone": customer.phone,
            },
            "status": conversation.status,
            "latest_message": message_text,
            "updated_at": conversation.updated_at,
        })

    return {
        "total": len(results),
        "conversations": results,
    }


# =====================================
# GET INDIVIDUAL CONVERSATION
# =====================================

@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    customer = db.get(
        Customer,
        conversation.customer_id,
    )

    messages = db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id
        )
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
    ).all()

    # Retrieve all AI drafts for this conversation
    drafts = db.scalars(
        select(ReplyDraft).where(
            ReplyDraft.conversation_id == conversation.id
        )
    ).all()

    # Map drafts to their corresponding messages
    draft_map = {
        draft.customer_message_id: draft
        for draft in drafts
    }

    message_results = []

    for message in messages:

        draft = draft_map.get(message.id)

        message_results.append({

            "message_id": str(message.id),

            "external_message_id": message.external_message_id,

            "sender_type": message.sender_type,

            "text": message.text,

            "created_at": message.created_at,

            "ai_draft": {

                "id": str(draft.id),

                "draft_text": draft.draft_text,

                "status": draft.status,

                "error_message": draft.error_message,

            } if draft else None,

        })

    return {

        "conversation_id": str(conversation.id),

        "customer": {
            "id": customer.external_customer_id,
            "name": customer.name,
            "phone": customer.phone,
        },

        "status": conversation.status,

        "messages": message_results,

    }

# =====================================
# EDIT AI DRAFT
# =====================================

@router.patch("/drafts/{draft_id}")
def edit_draft(
    draft_id: UUID,
    request: DraftUpdateRequest,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    draft = db.get(ReplyDraft, draft_id)

    if draft is None:
        raise HTTPException(
            status_code=404,
            detail="Draft not found",
        )

    if draft.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending drafts can be edited",
        )

    draft.draft_text = request.draft_text.strip()

    if not draft.draft_text:
        raise HTTPException(
            status_code=400,
            detail="Draft text cannot be empty",
        )

    db.commit()
    db.refresh(draft)

    return {
        "message": "Draft updated successfully",
        "draft_id": str(draft.id),
        "draft_text": draft.draft_text,
        "status": draft.status,
    }

@router.post("/drafts/{draft_id}/approve")
def approve_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    draft = db.get(ReplyDraft, draft_id)

    if draft is None:
        raise HTTPException(
            status_code= 404,
            detail = "Draft not found",
        )

    if draft.status != "pending":
        raise HTTPException(
            status_code=404,
            detail = "Only pending drafts can be approved",
        )

    if not draft.draft_text or not draft.draft_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Draft text cannot be empty",
        )

    try:
        agent_message = Message(
            conversation_id = draft.conversation_id,
            sender_type = "agent",
            text = draft.draft_text.strip(),
            external_message_id = None,
        )

        db.add(agent_message)

        draft.status = "approved"
        draft.approved_by = current_agent.id
        draft.approved_at = datetime.now(timezone.utc)

        db.commit()

        db.refresh(agent_message)
        db.refresh(draft)

        return {
            "message": "Draft approved successfully",
            "draft_id" : str(draft.id),
            "agent_message_id": str(agent_message.id),
            "approved_by": str(current_agent.id),
            "approved_at": draft.approved_at,
            "status": draft.status,
            "approved_text": agent_message.text,
        }

    except Exception:
        db.rollback()
        raise

