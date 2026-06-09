from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    skills: List[str] = []


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    skills: List[str]
    availability: float
    performance_score: float
    created_at: datetime
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    name: str
    description: str
    deadline_days: Optional[int] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    progress: float
    autonomy_score: float
    risk_level: str
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    required_skills: List[str]
    estimated_hours: Optional[float]
    actual_hours: float
    delay_probability: float
    ai_generated: bool
    assignee_id: Optional[str]
    dependencies: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class UpdateSubmit(BaseModel):
    task_id: str
    text: str


class UpdateOut(BaseModel):
    id: str
    raw_text: str
    parsed_progress: Optional[float]
    parsed_blocker: Optional[str]
    parsed_sentiment: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}