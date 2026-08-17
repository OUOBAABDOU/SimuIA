from __future__ import annotations

from livekit import api


async def start_room_recording(room_name: str, storage_bucket: str, filepath: str):
    """Start a composite MP4 recording for a LiveKit room.

    Storage credentials remain in the Egress service configuration in production;
    the request only supplies the destination path. This keeps media credentials
    out of application-level requests.
    """
    settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings()
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise RuntimeError("LIVEKIT_NOT_CONFIGURED")

    async with api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    ) as lkapi:
        info = await lkapi.egress.start_room_composite_egress(
            api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="speaker",
                file_outputs=[
                    api.EncodedFileOutput(
                        file_type=api.EncodedFileType.MP4,
                        filepath=filepath,
                    )
                ],
            )
        )
        return info
