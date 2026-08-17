from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException

from livekit import api

from app.core.config import get_settings


def create_join_token(*, room_name: str, identity: str, display_name: str | None = None) -> str:
    settings = get_settings()
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(status_code=503, detail="LIVEKIT_NOT_CONFIGURED")

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(display_name or identity)
        .with_ttl(timedelta(seconds=settings.livekit_token_ttl_seconds))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
                can_publish_sources=["camera", "microphone"],
            )
        )
    )
    return token.to_jwt()
