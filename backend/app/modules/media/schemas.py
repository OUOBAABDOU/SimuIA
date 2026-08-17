from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RecordingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interview_id: UUID | None
    room_name: str
    egress_id: str | None
    kind: str
    status: str
    storage_bucket: str
    storage_key: str | None
    mime_type: str | None
    file_size_bytes: int | None
    duration_seconds: int | None
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
