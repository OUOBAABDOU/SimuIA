"""Compatibility bridge for the MVP migration chain.

The source archive omitted the original 0004 revision. This revision is
intentionally schema-neutral so existing databases at 0002 can advance to
the persisted background-job revision without inventing incompatible tables.
"""
revision = "0004_mvp_core_bridge"
down_revision = "0002_auth_core"
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
