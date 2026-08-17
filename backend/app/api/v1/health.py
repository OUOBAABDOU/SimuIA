from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
import redis
import urllib.request

from app.database.session import get_db
from app.core.config import get_settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@router.get("/health/ai")
async def ai_health() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "status": "configured" if (settings.vertex_ai_enabled and settings.google_cloud_project) or settings.gemini_api_key else "not_configured",
        "provider": "vertex_ai" if settings.vertex_ai_enabled else settings.ai_provider,
        "model": settings.gemini_model,
        "vertex_ai": settings.vertex_ai_enabled,
    }

@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["postgresql"] = "ok"
    except Exception:
        checks["postgresql"] = "failed"
    try:
        s = get_settings()
        client = redis.Redis.from_url(s.redis_url, socket_connect_timeout=1, socket_timeout=1)
        checks["redis"] = "ok" if client.ping() else "failed"
        client.close()
    except Exception:
        checks["redis"] = "failed"
    try:
        s = get_settings()
        endpoint = s.media_s3_endpoint.rstrip("/") + "/minio/health/live"
        urllib.request.urlopen(endpoint, timeout=2).close()
        checks["minio"] = "ok"
    except Exception:
        checks["minio"] = "failed"
    ready = all(v == "ok" for v in checks.values())
    if not ready:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}
