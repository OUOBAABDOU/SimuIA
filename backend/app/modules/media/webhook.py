from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException, Request, Response
from sqlalchemy import select

from livekit.api import TokenVerifier, WebhookReceiver

from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.modules.jobs.service import enqueue_transcription
from app.modules.media.models import MediaRecording, RecordingStatus

router = APIRouter(prefix="/media", tags=["media"])


def _receiver() -> WebhookReceiver:
    s = get_settings()
    if not s.livekit_api_key or not s.livekit_api_secret:
        raise RuntimeError("LIVEKIT_NOT_CONFIGURED")
    return WebhookReceiver(TokenVerifier(s.livekit_api_key, s.livekit_api_secret))


@router.post("/livekit/webhook", include_in_schema=False)
async def livekit_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    if not authorization:
        raise HTTPException(status_code=401, detail="AUTHORIZATION_REQUIRED")

    body = (await request.body()).decode("utf-8")
    try:
        event = _receiver().receive(body, authorization)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="INVALID_LIVEKIT_WEBHOOK") from exc

    if event.event not in {"egress_started", "egress_updated", "egress_ended"}:
        return Response(status_code=204)

    info = event.egress_info
    egress_id = getattr(info, "egress_id", None)
    if not egress_id:
        return Response(status_code=204)

    async with AsyncSessionLocal() as db:
        recording = await db.scalar(
            select(MediaRecording).where(MediaRecording.egress_id == egress_id)
        )
        if recording is None:
            return Response(status_code=204)

        if event.event == "egress_ended" and recording.status in (
            RecordingStatus.PROCESSING, RecordingStatus.READY,
            RecordingStatus.FAILED, RecordingStatus.DELETED,
        ):
            return Response(status_code=204)

        if event.event == "egress_started":
            recording.status = RecordingStatus.RECORDING
            recording.started_at = recording.started_at or datetime.now(timezone.utc)
        elif event.event == "egress_ended":
            # A successful Egress must provide an output file. Without it, do not
            # let the pipeline hang forever: mark the recording/interview failed.
            file_results = getattr(info, "file_results", None) or []
            if not file_results:
                recording.status = RecordingStatus.FAILED
                recording.error_message = "EGRESS_COMPLETED_WITHOUT_FILE"
                if recording.interview_id:
                    from app.modules.interviews.models import Interview, InterviewStatus
                    interview = await db.get(Interview, recording.interview_id, with_for_update=True)
                    if interview and interview.status not in (InterviewStatus.COMPLETED, InterviewStatus.FAILED):
                        interview.status = InterviewStatus.FAILED
                await db.commit()
                return Response(status_code=204)

            recording.status = RecordingStatus.PROCESSING
            recording.completed_at = datetime.now(timezone.utc)
            result = file_results[0]
            filename = getattr(result, "filename", None)
            if filename:
                recording.storage_key = filename
            recording.file_size_bytes = getattr(result, "size", None) or recording.file_size_bytes
            duration = getattr(result, "duration", None)
            if duration is not None:
                recording.duration_seconds = int(duration / 1_000_000_000)
            recording.mime_type = "video/mp4"

            await db.flush()
            if recording.storage_key:
                await enqueue_transcription(db, recording.id)
        await db.commit()

    return Response(status_code=204)
