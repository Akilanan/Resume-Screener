from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, UserRole, Job, Resume, ResumeStatus
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func

router = APIRouter()
security = HTTPBearer()


def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = decode_token(credentials.credentials)
    if token_data.get("role") != UserRole.admin.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return token_data


@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user),
):
    total_users = db.query(User).count()
    total_jobs = db.query(Job).count()
    total_resumes = db.query(Resume).count()
    completed_resumes = db.query(Resume).filter(Resume.status == ResumeStatus.completed).count()

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_resumes": total_resumes,
        "completed_resumes": completed_resumes,
    }

@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user),
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "mfa_enabled": u.mfa_enabled,
            "created_at": u.created_at
        } for u in users
    ]


@router.get("/resumes")
def get_all_resumes(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user),
):
    resumes = db.query(Resume).order_by(Resume.uploaded_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "status": r.status.value if r.status else None,
            "score": r.score,
            "job_id": r.job_id,
            "match_summary": r.match_summary,
            "skills_matched": r.skills_matched,
            "skills_missing": r.skills_missing,
            "red_flags": r.red_flags,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        } for r in resumes
    ]
