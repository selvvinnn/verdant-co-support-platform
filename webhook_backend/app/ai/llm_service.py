import logging

from openai import OpenAI

from app.database import settings
from app.ai.prompt import SYSTEM_PROMPT


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.openai_api_key,
)


def generate_ai_reply(customer_message: str) -> str:

    if not customer_message or not customer_message.strip():
        raise ValueError("Customer message cannot be empty")

    try:

        response = client.responses.create(
            model=settings.openai_model,

            instructions=SYSTEM_PROMPT,

            input=f"""
CUSTOMER MESSAGE:

<customer_message>
{customer_message}
</customer_message>

Generate a suggested customer support reply.
""",

            max_output_tokens=250,
            store=False,
        )

        draft = response.output_text.strip()

        if not draft:
            raise ValueError("OpenAI returned an empty response")

        logger.info("AI draft generated successfully")

        return draft

    except Exception:

        logger.exception("OpenAI reply generation failed")

        raise