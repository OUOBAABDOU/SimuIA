import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.interviews.schemas import AnswerCreate
from app.modules.ai_providers.schemas import AIProviderCreate


def test_production_rejects_development_defaults() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production")


def test_media_answer_requires_recording() -> None:
    with pytest.raises(ValidationError):
        AnswerCreate(answer_type="AUDIO")


def test_text_answer_cannot_include_recording() -> None:
    with pytest.raises(ValidationError):
        AnswerCreate(text="answer", answer_type="TEXT", recording_id="00000000-0000-0000-0000-000000000001")


def test_gemini_provider_requires_api_key() -> None:
    with pytest.raises(ValidationError):
        AIProviderCreate(name="empty-gemini", provider="gemini")


def test_vertex_provider_requires_project() -> None:
    with pytest.raises(ValidationError):
        AIProviderCreate(name="empty-vertex", provider="vertex_ai")
