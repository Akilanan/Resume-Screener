from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Job
from app.schemas.job import JobCreate, JobResponse
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_token(credentials.credentials)


@router.post("/", response_model=JobResponse)
def create_job(
    request: JobCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    job = Job(
        title=request.title,
        description=request.description,
        created_by=current_user["sub"]
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs
