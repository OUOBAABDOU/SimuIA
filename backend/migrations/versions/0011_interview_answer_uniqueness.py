"""Prevent duplicate answers for the same interview question.
Revision ID: 0011_interview_answer_uniqueness
Revises: 0010_auth_sessions
"""
from alembic import op
import sqlalchemy as sa
revision = "0011_interview_answer_uniqueness"
down_revision = "0010_auth_sessions"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    constraints = inspector.get_unique_constraints("interview_answers")
    if not any(c["name"] == "uq_interview_answer_question" for c in constraints):
        op.create_unique_constraint("uq_interview_answer_question", "interview_answers", ["interview_id", "question_id"])

def downgrade() -> None:
    op.drop_constraint("uq_interview_answer_question", "interview_answers", type_="unique")
