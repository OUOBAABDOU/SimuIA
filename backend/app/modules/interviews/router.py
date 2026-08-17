from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db, AsyncSessionLocal
from app.modules.auth.dependencies import get_current_user
from app.modules.candidates.models import User
from app.modules.interviews.models import AnswerType, InterviewQuestion, InterviewStatus
from app.modules.interviews.service import create_interview, start_interview, answer_question, finish_interview, owned_interview
from app.modules.media.livekit import create_join_token
from app.modules.media.models import MediaRecording, RecordingKind, RecordingStatus
from app.core.config import get_settings
from app.modules.jobs.service import enqueue_evaluate_interview
from app.modules.interviews.schemas import AnswerCreate

router = APIRouter(prefix="/interviews", tags=["interviews"])

class CreateInterview(BaseModel): simulation_id: UUID
class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; simulation_id: UUID; status: str; current_question_index: int; started_at: datetime|None; completed_at: datetime|None; expires_at: datetime|None
class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; sequence: int; prompt: str
class AnswerRead(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; question_id: UUID; answer_type: str; text: str|None; recording_id: UUID|None; duration_seconds: int|None
class JoinRead(BaseModel): token: str; room_name: str; server_url: str
class ConsentCreate(BaseModel): accepted: bool

async def _read(i): return i

@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
async def create(payload: CreateInterview, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    i=await create_interview(db,user,payload.simulation_id); await db.commit(); await db.refresh(i); return i

@router.post("/{interview_id}/start", response_model=InterviewRead)
async def start(interview_id: UUID, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    i=await start_interview(db,user,interview_id); await db.commit(); await db.refresh(i); return i

@router.get("/{interview_id}/current-question", response_model=QuestionRead)
async def current_question(interview_id: UUID, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    i=await owned_interview(db,user,interview_id)
    q=await db.scalar(select(InterviewQuestion).where(InterviewQuestion.interview_id==i.id, InterviewQuestion.sequence==i.current_question_index))
    if q is None: raise HTTPException(404,"NO_CURRENT_QUESTION")
    if i.expires_at and datetime.now(timezone.utc)>=i.expires_at: raise HTTPException(409,"INTERVIEW_EXPIRED")
    return q

@router.post("/{interview_id}/questions/{question_id}/answer", response_model=AnswerRead, status_code=201)
async def answer(interview_id: UUID, question_id: UUID, payload: AnswerCreate, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    if payload.recording_id:
        r=await db.scalar(select(MediaRecording).where(MediaRecording.id==payload.recording_id, MediaRecording.interview_id==interview_id, MediaRecording.status == RecordingStatus.READY))
        if r is None: raise HTTPException(404,"RECORDING_NOT_FOUND")
    a=await answer_question(db,user,interview_id,question_id,text=payload.text,answer_type=payload.answer_type,recording_id=payload.recording_id,duration_seconds=payload.duration_seconds)
    await db.commit(); await db.refresh(a); return a

@router.post("/{interview_id}/finish", response_model=InterviewRead)
async def finish(interview_id: UUID, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    i=await finish_interview(db,user,interview_id)
    recordings = (await db.scalars(select(MediaRecording).where(MediaRecording.interview_id == i.id))).all()
    should_evaluate = not recordings or all(r.status in (RecordingStatus.READY, RecordingStatus.DELETED) for r in recordings)
    i.status = InterviewStatus.EVALUATING if should_evaluate else InterviewStatus.PROCESSING
    await db.commit()
    await db.refresh(i)
    if should_evaluate:
        async with AsyncSessionLocal() as job_db:
            await enqueue_evaluate_interview(job_db, i.id)
            await job_db.commit()
    return i

@router.post("/{interview_id}/join", response_model=JoinRead)
async def join(interview_id: UUID, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    i=await owned_interview(db,user,interview_id)
    if i.status not in ("ACTIVE",): raise HTTPException(409,"INTERVIEW_NOT_ACTIVE")
    if i.consent_given_at is None: raise HTTPException(409,"RECORDING_CONSENT_REQUIRED")
    profile_id=str(i.candidate_id); room=f"interview-{i.id}"
    token=create_join_token(room_name=room, identity=f"candidate:{profile_id}", display_name=user.email)
    existing=await db.scalar(select(MediaRecording).where(MediaRecording.interview_id==i.id, MediaRecording.room_name==room))
    if existing is None:
        existing = MediaRecording(
            candidate_id=i.candidate_id,
            interview_id=i.id,
            room_name=room,
            kind=RecordingKind.ROOM_COMPOSITE,
            status=RecordingStatus.REQUESTED,
            storage_bucket=get_settings().media_s3_bucket,
        )
        db.add(existing)
        await db.flush()

        from app.modules.media.recording import start_room_recording
        filepath = f"interviews/{i.id}/recordings/{existing.id}.mp4"
        egress = await start_room_recording(room, get_settings().media_s3_bucket, filepath)
        existing.egress_id = getattr(egress, "egress_id", None)
        existing.storage_key = filepath
        await db.commit()
    return {"token":token,"room_name":room,"server_url":get_settings().livekit_public_url}

@router.post("/{interview_id}/consent", status_code=status.HTTP_204_NO_CONTENT)
async def consent(interview_id: UUID, payload: ConsentCreate, db: AsyncSession=Depends(get_db), user: User=Depends(get_current_user)):
    if not payload.accepted:
        raise HTTPException(422,"RECORDING_CONSENT_REQUIRED")
    interview = await owned_interview(db,user,interview_id,lock=True)
    interview.consent_given_at = interview.consent_given_at or datetime.now(timezone.utc)
    await db.commit()
