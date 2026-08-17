from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from celery import Task
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.modules.jobs.models import BackgroundJob, JobStatus
from app.modules.interviews.models import Interview, InterviewStatus


async def _set_job(
    job_id: str,
    *,
    status: JobStatus,
    result: dict | None = None,
    error_message: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(BackgroundJob, uuid.UUID(job_id))
        if job is None:
            return
        job.status = status
        if started and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        if completed:
            job.completed_at = datetime.now(timezone.utc)
        if result is not None:
            job.result = result
        if error_message is not None:
            job.error_message = error_message
        await db.commit()


class IARHTask(Task):
    autoretry_for = (TimeoutError, ConnectionError)
    retry_backoff = True
    retry_backoff_max = 120
    retry_jitter = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id")
        if job_id:
            asyncio.run(_set_job(
                job_id,
                status=JobStatus.FAILURE,
                error_message=str(exc)[:4000],
                completed=True,
            ))
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id")
        if job_id:
            asyncio.run(_set_job(
                job_id,
                status=JobStatus.RETRY,
                error_message=str(exc)[:4000],
            ))
        return super().on_retry(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=IARHTask,
    name="app.tasks.health_check",
    ignore_result=False,
)
def health_check(self, *, job_id: str | None = None) -> dict:
    if job_id:
        asyncio.run(_set_job(job_id, status=JobStatus.STARTED, started=True))
    result = {"status": "ok", "worker": "celery"}
    if job_id:
        asyncio.run(_set_job(job_id, status=JobStatus.SUCCESS, result=result, completed=True))
    return result


@celery_app.task(
    bind=True,
    base=IARHTask,
    name="app.tasks.evaluate_interview",
)
def evaluate_interview(self, interview_id: str, *, job_id: str) -> dict:
    """Asynchronously evaluate a completed interview.

    The concrete AI service is deliberately imported inside the worker so
    API processes don't initialize the Gemini client unnecessarily.
    """
    asyncio.run(_set_job(job_id, status=JobStatus.STARTED, started=True))

    async def run():
        from app.ai.service import generate_report
        async with AsyncSessionLocal() as db:
            interview = await db.get(Interview, uuid.UUID(interview_id), with_for_update=True)
            if interview is None:
                raise ValueError("INTERVIEW_NOT_FOUND")
            if interview.status not in (InterviewStatus.EVALUATING, InterviewStatus.PROCESSING):
                raise ValueError(f"INTERVIEW_NOT_READY_FOR_EVALUATION:{interview.status.value}")
            interview.status = InterviewStatus.EVALUATING
            await db.flush()
            report = await generate_report(db, uuid.UUID(interview_id))
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)
            from app.modules.interviews.models import Simulation, SimulationStatus
            sim = await db.get(Simulation, interview.simulation_id, with_for_update=True)
            if sim:
                sim.status = SimulationStatus.COMPLETED
            await db.commit()
            return {"report_id": str(report.id)}

    try:
        result = asyncio.run(run())
    except Exception as exc:
        async def mark_evaluation_failed():
            async with AsyncSessionLocal() as db:
                interview = await db.get(Interview, uuid.UUID(interview_id), with_for_update=True)
                if interview and interview.status != InterviewStatus.COMPLETED:
                    interview.status = InterviewStatus.FAILED
                    await db.commit()
        asyncio.run(mark_evaluation_failed())
        raise
    asyncio.run(_set_job(job_id, status=JobStatus.SUCCESS, result=result, completed=True))
    return result


@celery_app.task(
    bind=True,
    base=IARHTask,
    name="app.tasks.transcribe_recording",
)
def transcribe_recording(self, recording_id: str, *, job_id: str) -> dict:
    asyncio.run(_set_job(job_id, status=JobStatus.STARTED, started=True))

    async def run():
        from sqlalchemy import select
        from app.modules.media.models import MediaRecording, RecordingStatus
        from app.modules.media.transcript_models import MediaTranscript, MediaTranscriptSegment
        from app.modules.media.storage import download_to_tempfile
        from app.modules.media.transcription import transcribe_file

        async with AsyncSessionLocal() as db:
            recording = await db.get(MediaRecording, uuid.UUID(recording_id))
            if recording is None:
                raise ValueError("RECORDING_NOT_FOUND")
            if not recording.storage_key:
                raise ValueError("RECORDING_STORAGE_KEY_MISSING")
            recording.status = RecordingStatus.PROCESSING
            interview = await db.get(Interview, recording.interview_id, with_for_update=True) if recording.interview_id else None
            if interview and interview.status == InterviewStatus.PROCESSING:
                interview.status = InterviewStatus.TRANSCRIBING
            await db.flush()

            media_path = download_to_tempfile(recording.storage_key, suffix=".mp4")
            text, segments = transcribe_file(media_path, suffix=".mp4")
            existing = await db.scalar(
                select(MediaTranscript).where(MediaTranscript.recording_id == recording.id)
            )
            if existing is not None:
                transcript = existing
                transcript.text = text
                transcript.provider = "faster-whisper"
                transcript.model = get_settings().whisper_model
                transcript.segments.clear()
            else:
                transcript = MediaTranscript(
                    recording_id=recording.id,
                    text=text,
                    provider="faster-whisper",
                    model=get_settings().whisper_model,
                )
                db.add(transcript)
                await db.flush()

            for i, row in enumerate(segments):
                db.add(MediaTranscriptSegment(
                    transcript_id=transcript.id,
                    sequence=i,
                    start_ms=row["start_ms"],
                    end_ms=row["end_ms"],
                    text=row["text"],
                ))
            recording.status = RecordingStatus.READY
            await db.flush()

            interview = await db.get(Interview, recording.interview_id, with_for_update=True) if recording.interview_id else None
            should_evaluate = False
            if interview and interview.status in (InterviewStatus.PROCESSING, InterviewStatus.TRANSCRIBING):
                recordings = (await db.scalars(select(MediaRecording).where(MediaRecording.interview_id == interview.id))).all()
                pending = [r for r in recordings if r.status not in (RecordingStatus.READY, RecordingStatus.DELETED)]
                if not pending:
                    interview.status = InterviewStatus.EVALUATING
                    should_evaluate = True
            await db.commit()

            if should_evaluate and interview is not None:
                from app.modules.jobs.service import enqueue_evaluate_interview
                async with AsyncSessionLocal() as job_db:
                    await enqueue_evaluate_interview(job_db, interview.id)
                    await job_db.commit()
            return {"recording_id": recording_id, "transcript_id": str(transcript.id), "evaluation_enqueued": should_evaluate}

    try:
        result = asyncio.run(run())
    except Exception as exc:
        async def mark_failed():
            async with AsyncSessionLocal() as db:
                recording = await db.get(__import__('app.modules.media.models', fromlist=['MediaRecording']).MediaRecording, uuid.UUID(recording_id))
                if recording:
                    recording.status = __import__('app.modules.media.models', fromlist=['RecordingStatus']).RecordingStatus.FAILED
                    recording.error_message = str(exc)[:4000]
                    if recording.interview_id:
                        interview = await db.get(Interview, recording.interview_id, with_for_update=True)
                        if interview and interview.status not in (InterviewStatus.COMPLETED, InterviewStatus.FAILED):
                            interview.status = InterviewStatus.FAILED
                await db.commit()
        asyncio.run(mark_failed())
        raise
    asyncio.run(_set_job(job_id, status=JobStatus.SUCCESS, result=result, completed=True))
    return result


@celery_app.task(
    bind=True,
    base=IARHTask,
    name="app.tasks.analyze_recording",
)
def analyze_recording(self, recording_id: str, *, job_id: str) -> dict:
    asyncio.run(_set_job(job_id, status=JobStatus.STARTED, started=True))

    async def run():
        from sqlalchemy import select
        from app.modules.media.models import MediaRecording
        from app.modules.media.transcript_models import MediaTranscript
        from app.modules.media.storage import download_bytes
        async with AsyncSessionLocal() as db:
            recording = await db.get(MediaRecording, uuid.UUID(recording_id))
            if recording is None:
                raise ValueError("RECORDING_NOT_FOUND")
            transcript = await db.scalar(
                select(MediaTranscript).where(MediaTranscript.recording_id == recording.id)
            )
            if transcript is None:
                raise ValueError("TRANSCRIPT_NOT_FOUND")
            # Analysis is intentionally a separate task boundary. The next
            # media-analysis lot consumes this transcript and never blocks
            # the recording/transcription pipeline.
            result = {"recording_id": recording_id, "transcript_id": str(transcript.id), "status": "READY_FOR_AI"}
            await db.commit()
            return result

    result = asyncio.run(run())
    asyncio.run(_set_job(job_id, status=JobStatus.SUCCESS, result=result, completed=True))
    return result


@celery_app.task(name="app.tasks.reconcile_stuck_jobs")
def reconcile_stuck_jobs(*, max_age_minutes: int = 60) -> dict:
    """Fail stale jobs so operators can retry them instead of leaving the UI hanging."""
    async def run() -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        changed = 0
        async with AsyncSessionLocal() as db:
            result = await db.scalars(select(BackgroundJob).where(
                BackgroundJob.status.in_([JobStatus.PENDING, JobStatus.STARTED, JobStatus.RETRY]),
                BackgroundJob.created_at < cutoff,
            ).with_for_update())
            for job in result.all():
                job.status = JobStatus.FAILURE
                job.error_message = "STALE_JOB_RECONCILIATED"
                job.completed_at = datetime.now(timezone.utc)
                changed += 1
            await db.commit()
        return changed

    return {"reconciled": asyncio.run(run())}
