import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.candidates.models import (
    CandidateProfile,
    Document,
    DocumentType,
    JobOffer,
    JobOfferSourceType,
    User,
    UserRole,
)


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 to run PostgreSQL integration tests.",
)


@pytest.fixture
async def db_session() -> AsyncSession:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://iarh:iarh@localhost:5432/iarh",
    )
    engine = create_async_engine(url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def test_candidate_core_crud(db_session: AsyncSession) -> None:
    email = f"db-test-{uuid.uuid4()}@example.test"

    user = User(
        email=email,
        password_hash="not-a-real-password-hash",
        role=UserRole.CANDIDATE,
    )
    user.profile = CandidateProfile(
        first_name="Test",
        last_name="Candidate",
        domain="Informatique",
        target_role="Développeur Backend",
    )
    user.profile.documents.append(
        Document(
            type=DocumentType.CV,
            file_name="cv.pdf",
            mime_type="application/pdf",
            storage_key=f"tests/{uuid.uuid4()}/cv.pdf",
            extracted_text="Python FastAPI PostgreSQL",
            parsed_data={"skills": ["Python", "FastAPI", "PostgreSQL"]},
        )
    )
    user.profile.job_offers.append(
        JobOffer(
            title="Développeur Backend",
            company_name="IARH Demo",
            source_type=JobOfferSourceType.TEXT,
            description="Construire des APIs Python.",
            parsed_data={"skills_required": ["Python", "FastAPI"]},
        )
    )

    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == email)
    )
    persisted_user = result.scalar_one()

    assert persisted_user.profile is not None
    assert len(persisted_user.profile.documents) == 1
    assert len(persisted_user.profile.job_offers) == 1

    await db_session.delete(persisted_user)
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == email)
    )
    assert result.scalar_one_or_none() is None
