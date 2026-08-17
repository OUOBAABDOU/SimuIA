import asyncio
from datetime import datetime, timedelta, timezone
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.credentials import decrypt_secret
from app.core.config import get_settings
from app.modules.ai_providers.models import AIProviderConfig

T = TypeVar("T", bound=BaseModel)


def _is_retryable(exc: Exception) -> bool:
    text = str(exc).upper()
    return any(code in text for code in ("429", "408", "500", "502", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))


def _generate_sync(schema: type[T], prompt: str, row: AIProviderConfig | None) -> T:
    from google import genai
    settings = get_settings()
    if row is None:
        if settings.vertex_ai_enabled:
            client = genai.Client(vertexai=True, project=settings.google_cloud_project, location=settings.google_cloud_location)
        else:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY_NOT_CONFIGURED")
            client = genai.Client(api_key=settings.gemini_api_key)
        model = settings.gemini_model
    elif row.provider == "vertex_ai":
        client = genai.Client(vertexai=True, project=row.project_id, location=row.location)
        model = row.model
    else:
        client = genai.Client(api_key=decrypt_secret(row.api_key_encrypted or ""))
        model = row.model
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_mime_type": "application/json", "response_json_schema": schema.model_json_schema()},
    )
    return schema.model_validate_json(response.text)


async def generate_json(db: AsyncSession, schema: type[T], prompt: str) -> T:
    settings = get_settings()
    if settings.vertex_ai_enabled and settings.google_cloud_project and not settings.ai_credential_encryption_key:
        return await asyncio.to_thread(_generate_sync, schema, prompt, None)
    rows = (await db.scalars(select(AIProviderConfig).where(
        AIProviderConfig.enabled.is_(True),
        (AIProviderConfig.cooldown_until.is_(None) | (AIProviderConfig.cooldown_until <= datetime.now(timezone.utc))),
    ).order_by(AIProviderConfig.priority, AIProviderConfig.last_used_at.nullsfirst()))).all()
    if not rows:
        return await asyncio.to_thread(_generate_sync, schema, prompt, None)
    last_error: Exception | None = None
    for row in rows:
        try:
            result = await asyncio.to_thread(_generate_sync, schema, prompt, row)
            row.failure_count = 0
            row.cooldown_until = None
            row.last_error = None
            row.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return result
        except Exception as exc:
            last_error = exc
            row.failure_count += 1
            row.last_error = str(exc)[:1000]
            if _is_retryable(exc):
                delay = min(900, 30 * (2 ** min(row.failure_count - 1, 5)))
                row.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=delay)
            else:
                row.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=5)
            await db.flush()
    await db.commit()
    raise RuntimeError(f"ALL_AI_PROVIDERS_FAILED: {last_error}")
