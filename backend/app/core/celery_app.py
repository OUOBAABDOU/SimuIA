from celery import Celery
from kombu import Queue

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "iarh",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("ai"),
        Queue("media"),
        Queue("transcription"),
    ),
    task_routes={
        "app.tasks.evaluate_interview": {"queue": "ai"},
        "app.tasks.transcribe_recording": {"queue": "transcription"},
        "app.tasks.analyze_recording": {"queue": "media"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=1800,
    task_soft_time_limit=1500,
    broker_transport_options={"visibility_timeout": 3600},
    result_backend_transport_options={
        "global_keyprefix": "iarh:",
        "retry_policy": {"timeout": 5.0},
    },
    result_expires=86400,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
    task_publish_retry=True,
    task_publish_retry_policy={"max_retries": 5, "interval_start": 1, "interval_step": 2, "interval_max": 10},
)

__all__ = ["celery_app"]
