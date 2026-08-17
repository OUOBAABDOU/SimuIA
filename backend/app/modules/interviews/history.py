from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.candidates.models import User, CandidateProfile
from app.modules.interviews.models import Interview, InterviewAnswer, InterviewQuestion, InterviewReport, Simulation
from app.modules.media.models import MediaRecording
from app.modules.media.transcript_models import MediaTranscript, MediaTranscriptSegment
from app.modules.media.storage import presigned_get_url

router = APIRouter(prefix="/interviews", tags=["interviews"])

class InterviewSummary(BaseModel):
    id: UUID
    simulation_id: UUID
    status: str
    current_question_index: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

class ProgressPoint(BaseModel):
    interview_id: UUID
    role: str
    score: float
    delta: float | None
    generated_at: datetime

class RecordingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    room_name: str
    status: str
    kind: str
    storage_bucket: str
    storage_key: str | None
    duration_seconds: int | None
    file_size_bytes: int | None

class TranscriptSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sequence: int
    start_ms: int
    end_ms: int
    text: str

class TranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    recording_id: UUID
    language: str | None
    text: str
    duration_ms: int | None
    provider: str
    model: str | None
    segments: list[TranscriptSegmentRead]

class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    interview_id: UUID
    global_score: float
    summary: str
    strengths: list
    weaknesses: list
    recommendations: list
    competency_scores: dict
    provider: str | None
    model: str | None
    generated_at: datetime

async def _owned_interview(db: AsyncSession, user: User, interview_id: UUID) -> Interview:
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="CANDIDATE_PROFILE_REQUIRED")
    interview = await db.scalar(select(Interview).where(
        Interview.id == interview_id,
        Interview.candidate_id == profile.id,
    ))
    if interview is None:
        raise HTTPException(status_code=404, detail="INTERVIEW_NOT_FOUND")
    return interview

@router.get("", response_model=list[InterviewSummary])
async def list_interviews(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="CANDIDATE_PROFILE_REQUIRED")
    result = await db.scalars(select(Interview).where(
        Interview.candidate_id == profile.id
    ).order_by(Interview.created_at.desc()))
    return list(result)

@router.get("/progress", response_model=list[ProgressPoint])
async def progress(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="CANDIDATE_PROFILE_REQUIRED")
    rows = (await db.execute(
        select(InterviewReport, Simulation.role)
        .join(Interview, InterviewReport.interview_id == Interview.id)
        .join(Simulation, Interview.simulation_id == Simulation.id)
        .where(Interview.candidate_id == profile.id)
        .order_by(InterviewReport.generated_at.asc())
    )).all()
    previous: float | None = None
    result = []
    for report, role in rows:
        score = float(report.global_score)
        result.append(ProgressPoint(
            interview_id=report.interview_id,
            role=role,
            score=score,
            delta=None if previous is None else round(score - previous, 2),
            generated_at=report.generated_at,
        ))
        previous = score
    return result

@router.get("/{interview_id}", response_model=InterviewSummary)
async def get_interview(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _owned_interview(db, user, interview_id)

@router.get("/{interview_id}/recordings", response_model=list[RecordingSummary])
async def list_recordings(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _owned_interview(db, user, interview_id)
    result = await db.scalars(select(MediaRecording).where(
        MediaRecording.interview_id == interview_id
    ).order_by(MediaRecording.requested_at.desc()))
    return list(result)

@router.get("/{interview_id}/transcripts/{recording_id}", response_model=TranscriptRead)
async def get_transcript(interview_id: UUID, recording_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _owned_interview(db, user, interview_id)
    recording = await db.scalar(select(MediaRecording).where(
        MediaRecording.id == recording_id, MediaRecording.interview_id == interview_id
    ))
    if recording is None:
        raise HTTPException(status_code=404, detail="RECORDING_NOT_FOUND")
    transcript = await db.scalar(select(MediaTranscript).where(MediaTranscript.recording_id == recording_id))
    if transcript is None:
        raise HTTPException(status_code=404, detail="TRANSCRIPT_NOT_FOUND")
    segments = await db.scalars(select(MediaTranscriptSegment).where(
        MediaTranscriptSegment.transcript_id == transcript.id
    ).order_by(MediaTranscriptSegment.sequence))
    data = TranscriptRead.model_validate(transcript)
    data.segments = [TranscriptSegmentRead.model_validate(x) for x in segments]
    return data

@router.get("/{interview_id}/report", response_model=ReportRead)
async def get_report(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _owned_interview(db, user, interview_id)
    report = await db.scalar(select(InterviewReport).where(InterviewReport.interview_id == interview_id))
    if report is None:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")
    return report


@router.get("/{interview_id}/recordings/{recording_id}/download")
async def get_recording_download_url(
    interview_id: UUID, recording_id: UUID,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    await _owned_interview(db, user, interview_id)
    recording = await db.scalar(select(MediaRecording).where(
        MediaRecording.id == recording_id,
        MediaRecording.interview_id == interview_id,
    ))
    if recording is None:
        raise HTTPException(status_code=404, detail="RECORDING_NOT_FOUND")
    if recording.status.value != "READY" or not recording.storage_key:
        raise HTTPException(status_code=409, detail="RECORDING_NOT_READY")
    return {"url": presigned_get_url(recording.storage_key)}
