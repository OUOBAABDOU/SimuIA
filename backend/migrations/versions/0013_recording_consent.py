"""record explicit recording consent on interviews"""
from alembic import op
import sqlalchemy as sa

revision = "0013_recording_consent"
down_revision = "0012_interview_processing_states"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("interviews", sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column("interviews", "consent_given_at")
