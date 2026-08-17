from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AIProviderCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    provider: str = Field(default="gemini", pattern="^(gemini|vertex_ai)$")
    api_key: str | None = Field(default=None, min_length=20, max_length=500)
    project_id: str | None = Field(default=None, max_length=255)
    location: str = Field(default="us-central1", max_length=80)
    model: str = Field(default="gemini-3.5-flash", max_length=120)
    priority: int = Field(default=100, ge=0, le=10000)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_provider(self) -> "AIProviderCreate":
        if self.provider == "gemini" and not self.api_key:
            raise ValueError("api_key is required for Gemini API providers")
        if self.provider == "vertex_ai" and not self.project_id:
            raise ValueError("project_id is required for Vertex AI providers")
        return self


class AIProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    api_key: str | None = Field(default=None, min_length=20, max_length=500)
    project_id: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    priority: int | None = Field(default=None, ge=0, le=10000)
    enabled: bool | None = None


class AIProviderRead(BaseModel):
    id: UUID
    name: str
    provider: str
    project_id: str | None
    location: str
    model: str
    priority: int
    enabled: bool
    failure_count: int
    cooldown_until: datetime | None
    last_error: str | None
    last_used_at: datetime | None
