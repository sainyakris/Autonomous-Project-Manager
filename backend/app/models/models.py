import uuid
import enum
from sqlalchemy import (
    Column, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, enum.Enum):
    REASSIGN = "reassign"
    REPRIORITIZE = "reprioritize"
    DEADLINE_ADJUST = "deadline_adjust"
    ESCALATE = "escalate"
    FLAG_RISK = "flag_risk"


class DecisionStatus(str, enum.Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    ESCALATED = "escalated"
    OVERRIDDEN = "overridden"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    skills = Column(JSON, default=list)
    availability = Column(Float, default=1.0)
    performance_score = Column(Float, default=0.75)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="assignee")
    updates = relationship("TaskUpdate", back_populates="author")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    deadline = Column(DateTime(timezone=True))
    progress = Column(Float, default=0.0)
    autonomy_score = Column(Float, default=0.0)
    risk_level = Column(String, default="low")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    client_reports = relationship("ClientReport", back_populates="project")
    decisions = relationship("AIDecision", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM)
    required_skills = Column(JSON, default=list)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    deadline = Column(DateTime(timezone=True))
    dependencies = Column(JSON, default=list)
    ai_generated = Column(Boolean, default=False)
    delay_probability = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
    updates = relationship("TaskUpdate", back_populates="task")
    subtasks = relationship("Task", backref="parent", remote_side=[id])


class TaskUpdate(Base):
    __tablename__ = "task_updates"

    id = Column(String, primary_key=True, default=gen_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_progress = Column(Float)
    parsed_blocker = Column(Text)
    parsed_sentiment = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="updates")
    author = relationship("User", back_populates="updates")


class ClientReport(Base):
    __tablename__ = "client_reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    approved = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="client_reports")


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    decision_type = Column(SAEnum(DecisionType), nullable=False)
    status = Column(SAEnum(DecisionStatus), default=DecisionStatus.PENDING)
    confidence = Column(Float, nullable=False)
    confidence_threshold = Column(Float, default=0.75)
    reasoning = Column(Text)
    action_taken = Column(JSON)
    human_override = Column(JSON)
    outcome_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="decisions")