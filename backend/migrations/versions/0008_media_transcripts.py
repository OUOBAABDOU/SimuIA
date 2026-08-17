"""add media transcripts and timestamped segments"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_media_transcripts"
down_revision = "0007_media_recordings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["recording_id"], ["media_recordings.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "media_transcript_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transcript_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["transcript_id"], ["media_transcripts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_media_transcript_segments_transcript_id", "media_transcript_segments", ["transcript_id"])
    op.create_index("ix_media_transcripts_recording_id", "media_transcripts", ["recording_id"])


def downgrade() -> None:
    op.drop_index("ix_media_transcripts_recording_id", table_name="media_transcripts")
    op.drop_index("ix_media_transcript_segments_transcript_id", table_name="media_transcript_segments")
    op.drop_table("media_transcript_segments")
    op.drop_table("media_transcripts")
