from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.candidates.models import User, CandidateProfile
from app.modules.interviews.models import Simulation
from .schemas import SimulationCreate, SimulationRead

router = APIRouter(prefix="/simulations", tags=["simulations"])

async def _candidate_id(db: AsyncSession, user: User) -> UUID:
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="CANDIDATE_PROFILE_REQUIRED")
    return profile.id

@router.post("", response_model=SimulationRead, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    payload: SimulationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate_id = await _candidate_id(db, user)
    simulation = Simulation(candidate_id=candidate_id, **payload.model_dump())
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)
    return simulation

@router.get("", response_model=list[SimulationRead])
async def list_simulations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate_id = await _candidate_id(db, user)
    result = await db.scalars(
        select(Simulation).where(Simulation.candidate_id == candidate_id)
        .order_by(Simulation.created_at.desc())
    )
    return list(result)

@router.get("/{simulation_id}", response_model=SimulationRead)
async def get_simulation(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate_id = await _candidate_id(db, user)
    simulation = await db.scalar(select(Simulation).where(
        Simulation.id == simulation_id, Simulation.candidate_id == candidate_id
    ))
    if simulation is None:
        raise HTTPException(status_code=404, detail="SIMULATION_NOT_FOUND")
    return simulation
