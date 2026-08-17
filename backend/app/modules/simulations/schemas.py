from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


SimulationCategory = Literal[
    "entretien_embauche",
    "examen_concours",
    "pitch_keynote",
    "competition_hackathon",
    "soutenance_devoir",
    "activite_pratique",
]


class SimulationCreate(BaseModel):
    category: SimulationCategory
    sector: str
    role: str = Field(min_length=1, max_length=200)
    experience_level: str
    interview_style: str
    mode: str
    total_questions: int = Field(default=8, ge=1, le=30)
    custom_scenario_text: str = ""
    selected_tech_stack: list[str] = Field(default_factory=list)


class SimulationRead(SimulationCreate):
    id: UUID
    status: Literal["DRAFT", "READY", "IN_PROGRESS", "COMPLETED", "CANCELLED"] = "DRAFT"


def new_simulation_id() -> UUID:
    return uuid4()
