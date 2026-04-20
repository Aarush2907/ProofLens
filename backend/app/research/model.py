import logging

from openai import OpenAI

from app.core.config import get_settings
from app.research.errors import ResearchError

logger = logging.getLogger(__name__)


def parse_model(schema, system: str, user: str):
    settings = get_settings()
    if not settings.openai_api_key:
        raise ResearchError("OpenAI API key is not configured.", retryable=False)

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    try:
        completion = client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=schema,
        )
    except Exception as exc:
        logger.warning("Model request failed: %s", exc.__class__.__name__)
        retryable = exc.__class__.__name__ not in {"AuthenticationError", "PermissionDeniedError"}
        raise ResearchError("The model request failed.", retryable=retryable) from exc

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ResearchError("The model returned an empty result.", retryable=True)
    return parsed
