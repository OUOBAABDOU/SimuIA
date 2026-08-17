"""Import all ORM models so SQLAlchemy/Alembic sees the complete metadata."""
from app.modules.candidates.models import CandidateProfile, Document, EmailVerificationToken, JobOffer, PasswordResetToken, User, RefreshToken
from app.modules.jobs.models import BackgroundJob
from app.modules.interviews.models import (
    Simulation, Interview, Competency, InterviewQuestion, InterviewAnswer,
    QuestionEvaluation, InterviewReport,
)
from app.modules.media.models import MediaRecording
from app.modules.media.transcript_models import MediaTranscript, MediaTranscriptSegment
from app.modules.ai_providers.models import AIProviderConfig
from app.modules.billing.models import Subscription

__all__ = [
    "CandidateProfile", "Document", "EmailVerificationToken", "JobOffer", "PasswordResetToken", "User", "RefreshToken", "BackgroundJob",
    "Simulation", "Interview", "Competency", "InterviewQuestion",
    "InterviewAnswer", "QuestionEvaluation", "InterviewReport",
    "MediaRecording", "MediaTranscript", "MediaTranscriptSegment", "AIProviderConfig", "Subscription",
]
