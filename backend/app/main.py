from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.modules.simulations.router import router as simulations_router
from app.modules.media.webhook import router as media_router
from app.modules.auth.router import router as auth_router
from app.modules.interviews.history import router as interview_history_router
from app.modules.interviews.router import router as interviews_router
from app.modules.ai_providers.router import router as ai_providers_router
from app.modules.billing.router import router as billing_router
from app.core.protection import audit_event, enforce_rate_limit

settings = get_settings()

app = FastAPI(
    title="IARH API",
    version="0.1.0",
    description="API de simulation d'entretiens et d'épreuves orales assistées par IA.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def protection_middleware(request: Request, call_next):
    try:
        await enforce_rate_limit(request)
        response = await call_next(request)
    except Exception as exc:
        from fastapi import HTTPException

        if isinstance(exc, HTTPException):
            audit_event("request_rejected", request, outcome=str(exc.status_code))
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
        raise
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not request.url.path.endswith("/health"):
        audit_event("state_change", request, outcome=str(response.status_code))
    return response

app.include_router(health_router, prefix="/api/v1")
app.include_router(simulations_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(interview_history_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(ai_providers_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
