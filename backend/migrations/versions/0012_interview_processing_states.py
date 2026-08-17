"""add explicit interview processing states for media and AI pipeline

Revision ID: 0012_interview_processing_states
Revises: 0011_interview_answer_uniqueness
"""
from alembic import op

revision = "0012_interview_processing_states"
down_revision = "0011_interview_answer_uniqueness"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TYPE interview_status ADD VALUE IF NOT EXISTS 'PROCESSING'")
    op.execute("ALTER TYPE interview_status ADD VALUE IF NOT EXISTS 'TRANSCRIBING'")
    op.execute("ALTER TYPE interview_status ADD VALUE IF NOT EXISTS 'EVALUATING'")
    op.execute("ALTER TYPE interview_status ADD VALUE IF NOT EXISTS 'FAILED'")

def downgrade() -> None:
    # PostgreSQL enums cannot safely remove values; downgrade is intentionally a no-op.
    pass
