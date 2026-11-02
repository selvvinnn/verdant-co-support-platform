from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Conversation, Message


def receive_customer_message(
    db: Session,
    *,
    customer_id: str,
    brand_id: str,
    name: str,
    phone: str,
    text: str,
    external_message_id: str | None = None,
    message_timestamp: datetime | None = None,
):

    # 1. Find existing customer
    customer = db.scalar(
        select(Customer)
        .where(
            Customer.external_customer_id == customer_id,
            Customer.brand_id == brand_id,
        )
        .with_for_update()
    )

    # 2. Create customer if not found
    if customer is None:

        customer = Customer(
            external_customer_id=customer_id,
            brand_id=brand_id,
            name=name,
            phone=phone,
        )

        db.add(customer)
        db.flush()

    else:

        customer.name = name
        customer.phone = phone

    # 3. Find existing open conversation
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.customer_id == customer.id,
            Conversation.status == "open",
        )
        .order_by(Conversation.created_at.desc())
        .with_for_update()
    )

    # 4. Create conversation if none exists
    if conversation is None:

        conversation = Conversation(
            customer_id=customer.id,
            status="open",
        )

        db.add(conversation)
        db.flush()

    # 5. Check duplicate message
    if external_message_id:

        existing_message = db.scalar(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.external_message_id == external_message_id,
            )
        )

        if existing_message:
            return conversation, existing_message, True

    # 6. Create message
    message = Message(
        conversation_id=conversation.id,
        external_message_id=external_message_id,
        sender_type="customer",
        text=text,
        created_at=message_timestamp or datetime.now(timezone.utc),
    )

    conversation.updated_at = datetime.now(timezone.utc)

    db.add(message)
    db.flush()

    return conversation, message, False