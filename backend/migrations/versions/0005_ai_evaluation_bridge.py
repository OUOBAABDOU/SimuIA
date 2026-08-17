"""Compatibility bridge for the AI migration chain.

The source archive omitted the original 0005 revision. It remains schema
neutral; AI/media tables are introduced by their explicit later migrations.
"""
revision = "0005_ai_evaluation_seed"
down_revision = "0004_mvp_core_bridge"
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
