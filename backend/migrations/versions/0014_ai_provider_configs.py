"""add encrypted multi-provider AI configuration pool"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014_ai_provider_configs"
down_revision = "0013_recording_consent"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "ai_provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="gemini"),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("project_id", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=80), nullable=False, server_default="us-central1"),
        sa.Column("model", sa.String(length=120), nullable=False, server_default="gemini-3.5-flash"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_ai_provider_configs_name"),
    )
    op.create_index("ix_ai_provider_configs_priority", "ai_provider_configs", ["priority", "enabled"])

def downgrade() -> None:
    op.drop_index("ix_ai_provider_configs_priority", table_name="ai_provider_configs")
    op.drop_table("ai_provider_configs")
