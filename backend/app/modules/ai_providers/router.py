from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.credentials import encrypt_secret
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_admin
from app.modules.candidates.models import User
from app.modules.ai_providers.models import AIProviderConfig
from app.modules.ai_providers.schemas import AIProviderCreate, AIProviderRead, AIProviderUpdate

router = APIRouter(prefix="/admin/ai-providers", tags=["admin-ai-providers"])


def _read(row: AIProviderConfig) -> AIProviderRead:
    return AIProviderRead.model_validate(row, from_attributes=True)


@router.get("", response_model=list[AIProviderRead])
async def list_providers(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = await db.scalars(select(AIProviderConfig).order_by(AIProviderConfig.priority, AIProviderConfig.name))
    return [_read(row) for row in rows]


@router.post("", response_model=AIProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(payload: AIProviderCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    if payload.provider == "gemini" and not payload.api_key:
        raise HTTPException(422, "GEMINI_API_KEY_REQUIRED")
    if payload.provider == "vertex_ai" and not payload.project_id:
        raise HTTPException(422, "GOOGLE_CLOUD_PROJECT_REQUIRED")
    row = AIProviderConfig(
        name=payload.name, provider=payload.provider,
        api_key_encrypted=encrypt_secret(payload.api_key) if payload.api_key else None,
        project_id=payload.project_id, location=payload.location, model=payload.model,
        priority=payload.priority, enabled=payload.enabled, created_by=admin.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _read(row)


@router.patch("/{provider_id}", response_model=AIProviderRead)
async def update_provider(provider_id: UUID, payload: AIProviderUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    row = await db.get(AIProviderConfig, provider_id)
    if row is None:
        raise HTTPException(404, "AI_PROVIDER_NOT_FOUND")
    values = payload.model_dump(exclude_unset=True)
    if "api_key" in values:
        row.api_key_encrypted = encrypt_secret(values.pop("api_key")) if values["api_key"] else None
    for key, value in values.items():
        setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _read(row)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    row = await db.get(AIProviderConfig, provider_id)
    if row is None:
        raise HTTPException(404, "AI_PROVIDER_NOT_FOUND")
    await db.delete(row)
    await db.commit()


@router.post("/{provider_id}/reset", response_model=AIProviderRead)
async def reset_provider(provider_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    row = await db.get(AIProviderConfig, provider_id)
    if row is None:
        raise HTTPException(404, "AI_PROVIDER_NOT_FOUND")
    row.failure_count = 0
    row.cooldown_until = None
    row.last_error = None
    row.enabled = True
    await db.commit()
    await db.refresh(row)
    return _read(row)
