# IARH architecture contract

## Active source tree

```text
backend/   FastAPI, SQLAlchemy, Alembic, Celery, Gemini/Vertex AI
frontend/  One Flutter application for Web and mobile targets
```

There is one API contract and one Flutter client source tree. Docker builds
only these active components plus the infrastructure services PostgreSQL,
Redis, MinIO, LiveKit and Egress.

## Development rule

Every feature follows this path:

```text
backend API/schema
    ↓
frontend service/model
    ↓
frontend Web + Android/iOS UI
    ↓
backend tests + frontend tests
```

The backend remains the only place for authentication, authorization, AI
provider selection, persistence and media access. Client applications never
contain provider secrets.
