from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.candidates.models import CandidateProfile, User
from app.modules.interviews.models import (
    Interview, InterviewAnswer, InterviewQuestion, InterviewStatus,
    Simulation, SimulationStatus, AnswerType, Competency,
)

QUESTION_TEMPLATES = [
    ("COMMUNICATION", "Présentez-vous brièvement et expliquez pourquoi ce poste correspond à votre projet professionnel."),
    ("EXPERIENCE", "Décrivez une réalisation professionnelle dont vous êtes particulièrement fier et votre contribution personnelle."),
    ("PROBLEM_SOLVING", "Parlez d'un problème complexe que vous avez rencontré. Comment avez-vous analysé la situation et choisi votre solution ?"),
    ("ADAPTABILITY", "Donnez un exemple d'une situation où vous avez dû vous adapter rapidement à un changement important."),
    ("MOTIVATION", "Pourquoi souhaitez-vous exercer ce rôle et quelles seraient vos priorités durant vos premiers mois ?"),
]

async def candidate_profile(db: AsyncSession, user: User) -> CandidateProfile:
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(409, "CANDIDATE_PROFILE_REQUIRED")
    return profile

async def owned_interview(db: AsyncSession, user: User, interview_id: UUID, *, lock: bool = False) -> Interview:
    profile = await candidate_profile(db, user)
    stmt = select(Interview).where(Interview.id == interview_id, Interview.candidate_id == profile.id)
    if lock:
        stmt = stmt.with_for_update()
    interview = await db.scalar(stmt)
    if interview is None:
        raise HTTPException(404, "INTERVIEW_NOT_FOUND")
    return interview

async def create_interview(db: AsyncSession, user: User, simulation_id: UUID) -> Interview:
    profile = await candidate_profile(db, user)
    simulation = await db.scalar(select(Simulation).where(
        Simulation.id == simulation_id, Simulation.candidate_id == profile.id
    ).with_for_update())
    if simulation is None:
        raise HTTPException(404, "SIMULATION_NOT_FOUND")
    if simulation.status in (SimulationStatus.COMPLETED, SimulationStatus.CANCELLED):
        raise HTTPException(409, "SIMULATION_NOT_STARTABLE")
    active = await db.scalar(select(Interview).where(
        Interview.simulation_id == simulation.id,
        Interview.status.in_([InterviewStatus.CREATED, InterviewStatus.ACTIVE, InterviewStatus.PAUSED]),
    ))
    if active:
        return active
    interview = Interview(simulation_id=simulation.id, candidate_id=profile.id, status=InterviewStatus.CREATED)
    db.add(interview)
    await db.flush()
    competencies = {c.code: c for c in (await db.scalars(select(Competency).where(Competency.active.is_(True)))).all()}
    count = simulation.total_questions
    for i in range(count):
        code, template = QUESTION_TEMPLATES[i % len(QUESTION_TEMPLATES)]
        competency = competencies.get(code)
        q = InterviewQuestion(
            interview_id=interview.id, competency_id=competency.id if competency else None,
            sequence=i, prompt=template, expected_signals=[], extra_metadata={"generated_by": "mvp_template"}
        )
        db.add(q)
    simulation.status = SimulationStatus.READY
    await db.flush()
    return interview

async def start_interview(db: AsyncSession, user: User, interview_id: UUID) -> Interview:
    interview = await owned_interview(db, user, interview_id, lock=True)
    if interview.status == InterviewStatus.COMPLETED:
        raise HTTPException(409, "INTERVIEW_ALREADY_COMPLETED")
    if interview.status == InterviewStatus.ACTIVE:
        return interview
    if interview.status not in (InterviewStatus.CREATED, InterviewStatus.PAUSED):
        raise HTTPException(409, "INTERVIEW_NOT_STARTABLE")
    now = datetime.now(timezone.utc)
    interview.status = InterviewStatus.ACTIVE
    interview.started_at = interview.started_at or now
    interview.expires_at = interview.expires_at or now + timedelta(minutes=get_settings().interview_duration_minutes)
    sim = await db.get(Simulation, interview.simulation_id, with_for_update=True)
    if sim: sim.status = SimulationStatus.IN_PROGRESS
    await db.flush()
    return interview

async def answer_question(db: AsyncSession, user: User, interview_id: UUID, question_id: UUID, *, text: str | None, answer_type: AnswerType = AnswerType.TEXT, recording_id: UUID | None = None, duration_seconds: int | None = None) -> InterviewAnswer:
    interview = await owned_interview(db, user, interview_id, lock=True)
    if interview.status != InterviewStatus.ACTIVE:
        raise HTTPException(409, "INTERVIEW_NOT_ACTIVE")
    now = datetime.now(timezone.utc)
    if interview.expires_at and now >= interview.expires_at:
        interview.status = InterviewStatus.ABORTED
        await db.flush()
        raise HTTPException(409, "INTERVIEW_EXPIRED")
    question = await db.scalar(select(InterviewQuestion).where(
        InterviewQuestion.id == question_id, InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence == interview.current_question_index,
    ))
    if question is None:
        raise HTTPException(409, "QUESTION_NOT_CURRENT")
    if answer_type == AnswerType.TEXT:
        if not (text and text.strip()) or recording_id is not None:
            raise HTTPException(422, "TEXT_ANSWER_REQUIRES_TEXT_ONLY")
    elif recording_id is None:
        raise HTTPException(422, "MEDIA_ANSWER_REQUIRES_RECORDING")
    existing = await db.scalar(select(InterviewAnswer).where(
        InterviewAnswer.interview_id == interview.id,
        InterviewAnswer.question_id == question.id,
    ))
    if existing is not None:
        raise HTTPException(409, "QUESTION_ALREADY_ANSWERED")
    answer = InterviewAnswer(interview_id=interview.id, question_id=question.id, answer_type=answer_type, text=text.strip() if text else None, recording_id=recording_id, duration_seconds=duration_seconds)
    db.add(answer)
    interview.current_question_index += 1
    await db.flush()
    return answer

async def finish_interview(db: AsyncSession, user: User, interview_id: UUID) -> Interview:
    interview = await owned_interview(db, user, interview_id, lock=True)
    if interview.status == InterviewStatus.COMPLETED:
        return interview
    if interview.status not in (InterviewStatus.ACTIVE, InterviewStatus.PAUSED):
        raise HTTPException(409, "INTERVIEW_NOT_FINISHABLE")
    total = await db.scalar(select(func.count(InterviewQuestion.id)).where(InterviewQuestion.interview_id == interview.id))
    answered = await db.scalar(select(func.count(InterviewAnswer.id)).where(InterviewAnswer.interview_id == interview.id))
    if answered < total:
        raise HTTPException(409, "ALL_QUESTIONS_NOT_ANSWERED")
    now = datetime.now(timezone.utc)
    interview.status = InterviewStatus.PROCESSING
    interview.completed_at = None
    await db.flush()
    return interview
