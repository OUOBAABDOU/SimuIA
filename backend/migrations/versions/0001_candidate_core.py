"""Create candidate core tables.

Revision ID: 0001_candidate_core
Revises:
Create Date: 2026-08-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_candidate_core"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # PostgreSQL ENUM types
    #
    # The ENUM types are created explicitly here.
    # create_type=False prevents SQLAlchemy from trying to create them
    # again when op.create_table() is executed.
    # ------------------------------------------------------------------

    user_role = postgresql.ENUM(
        "CANDIDATE",
        "ADMIN",
        name="user_role",
        create_type=False,
    )

    document_type = postgresql.ENUM(
        "CV",
        "COVER_LETTER",
        "OTHER",
        name="document_type",
        create_type=False,
    )

    job_offer_source_type = postgresql.ENUM(
        "TEXT",
        "FILE",
        "URL",
        name="job_offer_source_type",
        create_type=False,
    )

    # Create ENUM types only if they do not already exist.
    user_role.create(bind, checkfirst=True)
    document_type.create(bind, checkfirst=True)
    job_offer_source_type.create(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "role",
            user_role,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # Candidate profiles
    # ------------------------------------------------------------------

    op.create_table(
        "candidate_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "first_name",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "last_name",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "domain",
            sa.String(150),
            nullable=False,
        ),
        sa.Column(
            "target_role",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "phone",
            sa.String(30),
            nullable=True,
        ),
        sa.Column(
            "location",
            sa.String(150),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            name="uq_candidate_profiles_user_id",
        ),
    )

    # ------------------------------------------------------------------
    # Candidate documents
    # ------------------------------------------------------------------

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "type",
            document_type,
            nullable=False,
        ),
        sa.Column(
            "file_name",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "mime_type",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "storage_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "extracted_text",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "parsed_data",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "storage_key",
            name="uq_documents_storage_key",
        ),
    )

    op.create_index(
        "ix_documents_candidate_id",
        "documents",
        ["candidate_id"],
    )

    # ------------------------------------------------------------------
    # Job offers
    # ------------------------------------------------------------------

    op.create_table(
        "job_offers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "company_name",
            sa.String(200),
            nullable=True,
        ),
        sa.Column(
            "source_type",
            job_offer_source_type,
            nullable=False,
        ),
        sa.Column(
            "source_url",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "parsed_data",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_job_offers_candidate_id",
        "job_offers",
        ["candidate_id"],
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Drop tables first because they depend on the ENUM types.
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_job_offers_candidate_id",
        table_name="job_offers",
    )
    op.drop_table("job_offers")

    op.drop_index(
        "ix_documents_candidate_id",
        table_name="documents",
    )
    op.drop_table("documents")

    op.drop_table("candidate_profiles")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")

    # ------------------------------------------------------------------
    # Drop PostgreSQL ENUM types after dependent tables are removed.
    # ------------------------------------------------------------------

    bind = op.get_bind()

    postgresql.ENUM(
        name="job_offer_source_type",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        name="document_type",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        name="user_role",
    ).drop(bind, checkfirst=True)
