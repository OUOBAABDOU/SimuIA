from uuid import UUID, uuid4

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.modules.jobs.models import BackgroundJob, JobStatus


async def enqueue_evaluate_interview(db: AsyncSession, interview_id: UUID) -> BackgroundJob:
    job = BackgroundJob(
        task_name="app.tasks.evaluate_interview",
        status=JobStatus.PENDING,
        payload={"interview_id": str(interview_id)},
    )
    db.add(job)
    await db.flush()

    result = celery_app.send_task(
        "app.tasks.evaluate_interview",
        args=[str(interview_id)],
        kwargs={"job_id": str(job.id)},
        queue="ai",
        retry=True,
        retry_policy={"max_retries": 5, "interval_start": 1, "interval_step": 2, "interval_max": 10},
    )
    job.task_id = result.id
    await db.flush()
    return job


async def enqueue_transcription(db: AsyncSession, recording_id: UUID) -> BackgroundJob:
    job = BackgroundJob(
        task_name="app.tasks.transcribe_recording",
        status=JobStatus.PENDING,
        payload={"recording_id": str(recording_id)},
    )
    db.add(job)
    await db.flush()
    result = celery_app.send_task(
        "app.tasks.transcribe_recording",
        args=[str(recording_id)],
        kwargs={"job_id": str(job.id)},
        queue="transcription",
        retry=True,
        retry_policy={"max_retries": 5, "interval_start": 1, "interval_step": 2, "interval_max": 10},
    )
    job.task_id = result.id
    await db.flush()
    return job
