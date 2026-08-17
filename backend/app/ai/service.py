from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.ai.provider_pool import generate_json
from app.modules.interviews.models import (
    Interview, InterviewAnswer, InterviewQuestion, QuestionEvaluation,
    InterviewReport,
)


class EvaluationResult(BaseModel):
    score: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=5000)
    evidence: list[str] = Field(default_factory=list, max_length=8)


class ReportResult(BaseModel):
    summary: str = Field(min_length=1, max_length=10000)
    strengths: list[str] = Field(default_factory=list, max_length=10)
    weaknesses: list[str] = Field(default_factory=list, max_length=10)
    recommendations: list[str] = Field(default_factory=list, max_length=10)


def _client():
    from google import genai
    settings = get_settings()
    if settings.vertex_ai_enabled:
        if not settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT_NOT_CONFIGURED")
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY_NOT_CONFIGURED")
    return genai.Client(api_key=settings.gemini_api_key)


def _generate(model: type[BaseModel], prompt: str) -> BaseModel:
    client = _client()
    settings = get_settings()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": model.model_json_schema(),
        },
    )
    return model.model_validate_json(response.text)


async def generate_report(db: AsyncSession, interview_id: UUID) -> InterviewReport:
    from sqlalchemy.orm import selectinload

    interview = await db.scalar(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.competency),
            selectinload(Interview.answers),
            selectinload(Interview.report),
            selectinload(Interview.recordings),
        )
        .where(Interview.id == interview_id)
    )
    if interview is None:
        raise ValueError("INTERVIEW_NOT_FOUND")

    if interview.report is not None:
        return interview.report

    from app.modules.media.transcript_models import MediaTranscript
    recording_ids = [a.recording_id for a in interview.answers if a.recording_id]
    transcripts = {}
    if recording_ids:
        rows = (await db.scalars(select(MediaTranscript).where(MediaTranscript.recording_id.in_(recording_ids)))).all()
        transcripts = {row.recording_id: row for row in rows}
        missing = [str(rid) for rid in recording_ids if rid not in transcripts]
        if missing:
            raise ValueError("TRANSCRIPT_NOT_READY")

    answers_by_question = {a.question_id: a for a in interview.answers}
    evaluations: list[QuestionEvaluation] = []

    for question in interview.questions:
        answer = answers_by_question.get(question.id)
        if answer is None:
            continue

        answer_text = (answer.text or "").strip()
        if answer.recording_id:
            answer_text = (transcripts[answer.recording_id].text or "").strip()
            if not answer_text:
                raise ValueError("TRANSCRIPT_EMPTY")

        prompt = f"""You are a professional interview evaluator.
Evaluate only the answer provided. Do not infer any sensitive or protected
characteristic about the candidate.

Question:
{question.prompt}

Compétence:
{question.competency.name if question.competency else "Générale"}

Réponse:
{answer_text}

Return a score from 0 to 100, factual feedback, and observable evidence
directly grounded in the answer. Respond in English."""
        result = await generate_json(db, EvaluationResult, prompt)
        score = max(0.0, min(100.0, float(result.score)))

        evaluation = QuestionEvaluation(
            question_id=question.id,
            answer_id=answer.id,
            competency_id=question.competency_id,
            score=score,
            feedback=result.feedback,
            evidence=result.evidence,
            provider=get_settings().ai_provider,
            model=get_settings().gemini_model,
            prompt_version="v1",
        )
        db.add(evaluation)
        evaluations.append(evaluation)

    await db.flush()

    weighted: dict[str, list[float]] = {}
    weights: dict[str, float] = {}
    for evaluation in evaluations:
        key = str(evaluation.competency_id or "general")
        weighted.setdefault(key, []).append(float(evaluation.score))
        weights[key] = 1.0

    competency_scores = {
        key: round(sum(values) / len(values), 2)
        for key, values in weighted.items() if values
    }
    all_scores = [float(e.score) for e in evaluations]
    global_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    summary_prompt = f"""Write a professional summary of this interview.
Backend-calculated overall score: {global_score}/100.
Competency scores: {competency_scores}.
Do not modify the scores. Produce a concise summary, strengths, weaknesses,
and concrete recommendations in English."""
    report_text = await generate_json(db, ReportResult, summary_prompt)

    report = InterviewReport(
        interview_id=interview.id,
        global_score=Decimal(str(global_score)),
        summary=report_text.summary,
        strengths=report_text.strengths,
        weaknesses=report_text.weaknesses,
        recommendations=report_text.recommendations,
        competency_scores=competency_scores,
        provider=get_settings().ai_provider,
        model=get_settings().gemini_model,
    )
    db.add(report)
    await db.flush()
    return report
