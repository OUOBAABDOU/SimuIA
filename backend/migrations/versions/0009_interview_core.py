"""restore the persistent interview domain and link media recordings

Revision ID: 0009_interview_core
Revises: 0008_media_transcripts
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_interview_core"
down_revision = "0008_media_transcripts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    simulation_status = postgresql.ENUM(
        "DRAFT", "READY", "IN_PROGRESS", "COMPLETED", "CANCELLED",
        name="simulation_status", create_type=False
    )
    interview_status = postgresql.ENUM(
        "CREATED", "ACTIVE", "PAUSED", "COMPLETED", "ABORTED",
        name="interview_status", create_type=False
    )
    answer_type = postgresql.ENUM(
        "TEXT", "AUDIO", "VIDEO", name="answer_type", create_type=False
    )
    for e in (simulation_status, interview_status, answer_type):
        e.create(bind, checkfirst=True)

    op.create_table(
        "simulations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("sector", sa.String(150), nullable=False),
        sa.Column("role", sa.String(200), nullable=False),
        sa.Column("experience_level", sa.String(80), nullable=False),
        sa.Column("interview_style", sa.String(80), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("custom_scenario_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("selected_tech_stack", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", simulation_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulations_candidate_id", "simulations", ["candidate_id"])

    op.create_table(
        "competencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("weight", sa.Numeric(6, 3), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", interview_status, nullable=False, server_default="CREATED"),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interviews_simulation_id", "interviews", ["simulation_id"])
    op.create_index("ix_interviews_candidate_id", "interviews", ["candidate_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competency_id", postgresql.UUID(as_uuid=True)),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected_signals", postgresql.JSONB()),
        sa.Column("metadata", postgresql.JSONB()),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interview_id", "sequence", name="uq_interview_question_sequence"),
    )
    op.create_index("ix_interview_questions_interview_id", "interview_questions", ["interview_id"])
    op.create_index("ix_interview_questions_competency_id", "interview_questions", ["competency_id"])

    op.create_table(
        "interview_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_type", answer_type, nullable=False, server_default="TEXT"),
        sa.Column("text", sa.Text()),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["interview_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recording_id"], ["media_recordings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ("interview_id", "question_id", "recording_id"):
        op.create_index(f"ix_interview_answers_{col}", "interview_answers", [col])

    op.create_table(
        "question_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competency_id", postgresql.UUID(as_uuid=True)),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB()),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120)),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["interview_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["answer_id"], ["interview_answers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ("question_id", "answer_id", "competency_id"):
        op.create_index(f"ix_question_evaluations_{col}", "question_evaluations", [col])

    op.create_table(
        "interview_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("global_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("weaknesses", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("competency_scores", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interview_id"),
    )

    # The old media migration intentionally kept interview_id nullable. Now
    # that interviews exist, enforce referential integrity while preserving
    # compatibility with recordings created before an interview was linked.
    op.create_foreign_key(
        "fk_media_recordings_interview_id",
        "media_recordings", "interviews",
        ["interview_id"], ["id"], ondelete="SET NULL",
    )

    # Seed stable MVP competencies. UUIDs are generated by PostgreSQL.
    competencies = [
        ("COMMUNICATION", "Communication", "Clarity, structure and relevance of oral communication.", 1.0),
        ("PROBLEM_SOLVING", "Résolution de problèmes", "Reasoning, diagnosis and solution quality.", 1.0),
        ("EXPERIENCE", "Expérience professionnelle", "Evidence and relevance of professional experience.", 1.0),
        ("ADAPTABILITY", "Adaptabilité", "Ability to adapt, learn and handle change.", 1.0),
        ("MOTIVATION", "Motivation", "Motivation, fit and understanding of the target role.", 1.0),
    ]
    op.bulk_insert(
        sa.table(
            "competencies",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("description", sa.Text),
            sa.column("weight", sa.Numeric),
            sa.column("active", sa.Boolean),
        ),
        [{"id": __import__("uuid").uuid4(), "code": c, "name": n, "description": d, "weight": w, "active": True}
         for c, n, d, w in competencies],
    )


def downgrade() -> None:
    op.drop_constraint("fk_media_recordings_interview_id", "media_recordings", type_="foreignkey")
    op.drop_table("interview_reports")
    for table, cols in [
        ("question_evaluations", ["question_id", "answer_id", "competency_id"]),
        ("interview_answers", ["interview_id", "question_id", "recording_id"]),
        ("interview_questions", ["interview_id", "competency_id"]),
        ("interviews", ["simulation_id", "candidate_id"]),
    ]:
        for col in cols:
            op.drop_index(f"ix_{table}_{col}", table_name=table)
        op.drop_table(table)
    op.drop_table("competencies")
    op.drop_index("ix_simulations_candidate_id", table_name="simulations")
    op.drop_table("simulations")
    for name in ("answer_type", "interview_status", "simulation_status"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
