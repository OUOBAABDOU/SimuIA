"""add media recording persistence

Revision ID: 0007_media_recordings
Revises: 0006_background_jobs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_media_recordings"
down_revision = "0006_background_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE recording_kind AS ENUM ('ROOM_COMPOSITE', 'AUDIO', 'VIDEO');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE recording_status AS ENUM ('REQUESTED', 'RECORDING', 'PROCESSING', 'READY', 'FAILED', 'DELETED');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)
    recording_kind = postgresql.ENUM(
        "ROOM_COMPOSITE", "AUDIO", "VIDEO", name="recording_kind", create_type=False
    )
    recording_status = postgresql.ENUM(
        "REQUESTED", "RECORDING", "PROCESSING", "READY", "FAILED", "DELETED",
        name="recording_status", create_type=False,
    )
    op.create_table(
        "media_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("room_name", sa.String(length=255), nullable=False),
        sa.Column("egress_id", sa.String(length=255), nullable=True),
        sa.Column("kind", recording_kind, nullable=False),
        sa.Column("status", recording_status, nullable=False, server_default="REQUESTED"),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_name"),
        sa.UniqueConstraint("egress_id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_media_recordings_candidate_id", "media_recordings", ["candidate_id"])
    op.create_index("ix_media_recordings_interview_id", "media_recordings", ["interview_id"])
    op.create_index("ix_media_recordings_egress_id", "media_recordings", ["egress_id"])


def downgrade() -> None:
    op.drop_index("ix_media_recordings_egress_id", table_name="media_recordings")
    op.drop_index("ix_media_recordings_interview_id", table_name="media_recordings")
    op.drop_index("ix_media_recordings_candidate_id", table_name="media_recordings")
    op.drop_table("media_recordings")
    op.execute("DROP TYPE IF EXISTS recording_status")
    op.execute("DROP TYPE IF EXISTS recording_kind")
