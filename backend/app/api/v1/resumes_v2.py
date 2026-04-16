from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import get_db
from app.db.models import Resume, Job, ResumeStatus
from app.core.encryption import encrypt
from app.queue.producer import publish_resume_job
from app.core.security import decode_token
from app.core.audit import audit
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, ExpiredSignatureError
import uuid
import os
import shutil
import logging
from typing import List

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and return user payload
    
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    token = credentials.credentials
    
    # Validate token format
    if not token or token in ["null", "undefined", "None"]:
        logger.warning("Invalid token format received")
        raise AuthenticationError("Invalid token format")
    
    try:
        payload = decode_token(token)
        
        # Validate required fields
        if "sub" not in payload:
            logger.warning("Token missing 'sub' claim")
            raise AuthenticationError("Invalid token payload: missing subject")
        
        if "exp" not in payload:
            logger.warning("Token missing 'exp' claim")
            raise AuthenticationError("Invalid token: missing expiration")
        
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Expired token received")
        raise AuthenticationError("Token has expired. Please login again.")
    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise AuthenticationError(f"Invalid authentication credentials")
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise AuthenticationError("Authentication error")


@router.post("/upload/{job_id}")
async def upload_resumes(
    job_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload resumes for a specific job
    
    - **job_id**: The job ID to associate resumes with
    - **files**: List of PDF/DOCX files to upload
    """
    # Check files exist
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file sizes
    max_size = 10 * 1024 * 1024  # 10MB per file
    for file in files:
        # Check file type
        if not file.filename.endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.filename}. Only PDF and DOCX allowed"
            )
    
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check user has permission
    if job.created_by != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to upload to this job")

    results = []
    errors = []
    
    for file in files:
        try:
            resume_id = str(uuid.uuid4())
            save_path = f"/tmp/resumes/{resume_id}.pdf"
            os.makedirs("/tmp/resumes", exist_ok=True)

            # Save file
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Create database entry
            resume = Resume(
                id=resume_id,
                job_id=job_id,
                filename=file.filename,
                candidate_name_encrypted=encrypt("Unknown"),
                candidate_email_encrypted=encrypt("unknown@unknown.com"),
                status=ResumeStatus.queued,
            )
            db.add(resume)
            
            # Push to queue
            publish_resume_job({
                "resume_id": resume_id,
                "job_id": job_id,
                "file_path": save_path,
                "job_description": job.description,
            })
            
            results.append({
                "resume_id": resume_id,
                "filename": file.filename,
                "status": "queued"
            })
            
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})
    
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during upload: {e}")
        raise HTTPException(status_code=500, detail="Database error during upload")

    return {
        "uploaded": len(results),
        "resumes": results,
        "errors": errors,
        "job_id": job_id
    }


@router.get("/results/{job_id}")
def get_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get screening results for a job
    
    - **job_id**: The job ID to get results for
    """
    # Verify job exists and user has access
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.created_by != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    try:
        resumes = db.query(Resume).filter(Resume.job_id == job_id).order_by(Resume.score.desc()).all()
        
        return {
            "job_id": job_id,
            "total": len(resumes),
            "completed": len([r for r in resumes if r.status == ResumeStatus.completed]),
            "pending": len([r for r in resumes if r.status == ResumeStatus.queued]),
            "resumes": [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "status": r.status.value,
                    "score": r.score,
                    "match_summary": r.match_summary,
                    "skills_matched": r.skills_matched,
                    "skills_missing": r.skills_missing,
                    "red_flags": r.red_flags,
                    "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                    "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                }
                for r in resumes
            ]
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching results: {e}")
        raise HTTPException(status_code=500, detail="Error fetching results")


@router.post("/screen")
async def screen_resumes_direct(
    request: Request,
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Direct screening endpoint - creates a temp job and queues resumes
    
    - **job_description**: The job description to match against
    - **resumes**: List of resume files to screen
    """
    # Validate
    if not job_description or len(job_description) < 10:
        raise HTTPException(status_code=400, detail="Job description too short (min 10 chars)")
    
    if not resumes:
        raise HTTPException(status_code=400, detail="No resume files provided")
    
    if len(resumes) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per request")

    user_id = current_user["sub"]
    job_id = str(uuid.uuid4())
    
    try:
        from app.db.models import Job as JobModel
        
        # Create temporary job
        job = JobModel(
            id=job_id,
            title="Quick Screen",
            description=job_description,
            created_by=user_id,
        )
        db.add(job)
        db.commit()
        
        logger.info(f"Created quick screen job: {job_id} for user: {user_id}")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create screening job")

    # Log audit
    audit.log(
        user_id=user_id,
        action="SCREEN_RESUMES",
        resource="screening_job",
        resource_id=job_id,
        details={
            "num_resumes": len(resumes),
            "job_description_preview": job_description[:100],
            "source": "web"
        },
        request=request,
        success=True
    )

    queued = []
    errors = []
    
    for file in resumes:
        try:
            resume_id = str(uuid.uuid4())
            save_path = f"/tmp/resumes/{resume_id}.pdf"
            os.makedirs("/tmp/resumes", exist_ok=True)
            
            # Save file
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Create resume
            resume = Resume(
                id=resume_id,
                job_id=job_id,
                filename=file.filename,
                candidate_name_encrypted=encrypt("Unknown"),
                candidate_email_encrypted=encrypt("unknown@unknown.com"),
                status=ResumeStatus.queued,
            )
            db.add(resume)
            
            # Queue for processing
            publish_resume_job({
                "resume_id": resume_id,
                "job_id": job_id,
                "file_path": save_path,
                "job_description": job_description,
            })
            
            queued.append({"resume_id": resume_id, "filename": file.filename})
            
        except Exception as e:
            logger.error(f"Failed to queue file {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})
    
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to commit resumes: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "job_id": job_id,
        "total": len(queued),
        "queued": queued,
        "errors": errors,
        "message": f"Queued {len(queued)} resumes for processing",
        "status": "processing",
        "check_results_at": f"/api/v1/resumes/results/{job_id}"
    }


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "resumes-api",
        "timestamp": datetime.utcnow().isoformat()
    }
