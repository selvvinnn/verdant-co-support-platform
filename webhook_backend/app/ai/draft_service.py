import logging

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Message, ReplyDraft
from app.ai.llm_service import generate_ai_reply


logger = logging.getLogger(__name__)


def generate_draft_for_message(
    db: Session,
    conversation_id: UUID,
    message_id: UUID,
):

    # 1. Retrieve the customer message
    message = db.get(Message, message_id)

    if message is None:
        raise ValueError("Customer message not found")

    if message.conversation_id != conversation_id:
        raise ValueError("Message does not belong to conversation")

    if message.sender_type != "customer":
        raise ValueError("AI drafts can only answer customer messages")

    # 2. Check whether a draft already exists
    existing_draft = db.scalar(
        select(ReplyDraft).where(
            ReplyDraft.customer_message_id == message_id
        )
    )

    if existing_draft and existing_draft.status != "failed":
        return existing_draft

    try:

        # 3. Generate AI reply
        draft_text = generate_ai_reply(message.text)

        # 4. Create or retry the draft
        if existing_draft:

            existing_draft.draft_text = draft_text
            existing_draft.status = "pending"
            existing_draft.error_message = None

            draft = existing_draft

        else:

            draft = ReplyDraft(
                conversation_id=conversation_id,
                customer_message_id=message_id,
                draft_text=draft_text,
                status="pending",
            )

            db.add(draft)

        # 5. Save draft
        db.commit()
        db.refresh(draft)

        return draft

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Draft generation failed for message %s",
            message_id,
        )

        # 6. Persist failure so an agent can see it
        # and the system can retry later.
        failed_draft = db.scalar(
            select(ReplyDraft).where(
                ReplyDraft.customer_message_id == message_id
            )
        )

        if failed_draft is None:

            failed_draft = ReplyDraft(
                conversation_id=conversation_id,
                customer_message_id=message_id,
                draft_text=None,
                status="failed",
                error_message=str(exc)[:500],
            )

            db.add(failed_draft)

        else:

            failed_draft.status = "failed"
            failed_draft.error_message = str(exc)[:500]

        db.commit()

        return failed_draft