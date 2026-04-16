from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Resume, Job, ResumeStatus
from app.core.encryption import encrypt
from app.queue.producer import publish_resume_job
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import os
import shutil
from typing import List

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_token(credentials.credentials)


@router.post("/upload/{job_id}")
async def upload_resumes(
    job_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = []
    for file in files:
        resume_id = str(uuid.uuid4())
        save_path = f"/tmp/resumes/{resume_id}.pdf"
        os.makedirs("/tmp/resumes", exist_ok=True)

        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        resume = Resume(
            id=resume_id,
            job_id=job_id,
            filename=file.filename,
            # PII encrypted before storing
            candidate_name_encrypted=encrypt("Unknown"),
            candidate_email_encrypted=encrypt("unknown@unknown.com"),
            status=ResumeStatus.queued,
        )
        db.add(resume)
        db.commit()

        # Push to queue for async processing
        publish_resume_job({
            "resume_id": resume_id,
            "job_id": job_id,
            "file_path": save_path,
            "job_description": job.description,
        })
        results.append({"resume_id": resume_id, "filename": file.filename, "status": "queued"})

    return {"uploaded": len(results), "resumes": results}


@router.get("/results/{job_id}")
def get_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    resumes = db.query(Resume).filter(Resume.job_id == job_id).order_by(Resume.score.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "status": r.status,
            "score": r.score,
            "match_summary": r.match_summary,
            "skills_matched": r.skills_matched,
            "skills_missing": r.skills_missing,
            "red_flags": r.red_flags,
        }
        for r in resumes
    ]


@router.post("/screen")
async def screen_resumes_direct(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Direct screening endpoint — creates a temp job and queues resumes."""
    job_id = str(uuid.uuid4())
    from app.db.models import Job as JobModel
    job = JobModel(
        id=job_id,
        title="Quick Screen",
        description=job_description,
        created_by=current_user["sub"],
    )
    db.add(job)
    db.commit()

    queued = []
    for file in resumes:
        resume_id = str(uuid.uuid4())
        save_path = f"/tmp/resumes/{resume_id}.pdf"
        os.makedirs("/tmp/resumes", exist_ok=True)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        resume = Resume(
            id=resume_id,
            job_id=job_id,
            filename=file.filename,
            candidate_name_encrypted=encrypt("Unknown"),
            candidate_email_encrypted=encrypt("unknown@unknown.com"),
            status=ResumeStatus.queued,
        )
        db.add(resume)
        db.commit()

        publish_resume_job({
            "resume_id": resume_id,
            "job_id": job_id,
            "file_path": save_path,
            "job_description": job_description,
        })
        queued.append({"resume_id": resume_id, "filename": file.filename})

    return {
        "job_id": job_id,
        "total": len(queued),
        "results": [
            {
                "filename": r["filename"],
                "match_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "summary": "Processing in background...",
            }
            for r in queued
        ],
        "job_description": job_description,
    }
