import json
from typing import TypeVar

from groq import APIError, AsyncGroq
from pydantic import BaseModel, ValidationError

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the model can't give us usable output."""


_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY is not set")
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


async def generate_structured(
    system: str, user: str, schema: type[T], max_retries: int = 1
) -> T:
    """Ask the model for JSON, validate it against `schema`, retry on bad output."""
    messages = [
        {
            "role": "system",
            "content": system
            + "\n\nRespond with a single JSON object matching this JSON schema:\n"
            + json.dumps(schema.model_json_schema()),
        },
        {"role": "user", "content": user},
    ]
    last_error: Exception | None = None

    for _ in range(max_retries + 1):
        try:
            response = await get_client().chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except APIError as e:
            raise LLMError(f"Groq API error: {e}") from e

        raw = response.choices[0].message.content or ""
        try:
            return schema.model_validate_json(raw)
        except ValidationError as e:
            last_error = e
            # Show the model its own bad answer and what was wrong with it
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {"role": "user", "content": f"That JSON was invalid: {e}. Return corrected JSON only."}
            )

    raise LLMError(f"Model returned invalid output after {max_retries + 1} attempts: {last_error}")