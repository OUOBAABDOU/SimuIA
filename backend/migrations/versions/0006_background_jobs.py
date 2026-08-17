"""add persistent background jobs

Revision ID: 0006_background_jobs
Revises: 0002_auth_core
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_background_jobs"
down_revision = "0005_ai_evaluation_seed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    job_status = sa.Enum(
        "PENDING", "STARTED", "RETRY", "SUCCESS", "FAILURE",
        name="job_status",
    )
    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_name", sa.String(length=150), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("status", job_status, nullable=False, server_default="PENDING"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_background_jobs_task_name", "background_jobs", ["task_name"])
    op.create_index("ix_background_jobs_task_id", "background_jobs", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_background_jobs_task_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_task_name", table_name="background_jobs")
    op.drop_table("background_jobs")
    sa.Enum(name="job_status").drop(op.get_bind(), checkfirst=True)
