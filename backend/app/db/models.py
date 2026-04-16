from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    hr = "hr"


class JobStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class ResumeStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)  # NOT encrypted — used for login
    name_encrypted = Column(String, nullable=False)  # PII — encrypted
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.hr)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    jobs = relationship("Job", back_populates="created_by_user")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.open)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job")


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    # PII — ALL candidate info encrypted
    candidate_name_encrypted = Column(String)
    candidate_email_encrypted = Column(String)
    filename = Column(String, nullable=False)
    status = Column(Enum(ResumeStatus), default=ResumeStatus.queued)
    score = Column(Float, nullable=True)
    match_summary = Column(Text, nullable=True)  # LLM output
    skills_matched = Column(Text, nullable=True)  # JSON string
    skills_missing = Column(Text, nullable=True)  # JSON string
    red_flags = Column(Text, nullable=True)  # JSON string
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    job = relationship("Job", back_populates="resumes")
