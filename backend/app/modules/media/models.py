import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RecordingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    RECORDING = "RECORDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    DELETED = "DELETED"


class RecordingKind(str, enum.Enum):
    ROOM_COMPOSITE = "ROOM_COMPOSITE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"


class MediaRecording(Base):
    __tablename__ = "media_recordings"
    __table_args__ = (UniqueConstraint("egress_id", name="media_recordings_egress_id_key"), Index("ix_media_recordings_egress_id", "egress_id"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Kept nullable until the consolidated interview migration is applied.
    interview_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interviews.id", ondelete="SET NULL"), index=True
    )
    room_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    egress_id: Mapped[str | None] = mapped_column(String(255))
    kind: Mapped[RecordingKind] = mapped_column(
        Enum(RecordingKind, name="recording_kind"), nullable=False
    )
    status: Mapped[RecordingStatus] = mapped_column(
        Enum(RecordingStatus, name="recording_status"),
        nullable=False,
        default=RecordingStatus.REQUESTED,
    )
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(Text, unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    interview = relationship("Interview", back_populates="recordings")

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate = relationship("CandidateProfile")
