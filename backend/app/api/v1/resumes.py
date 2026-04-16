from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import get_db
from app.db.models import Resume, Job, ResumeStatus
from app.core.encryption import encrypt
from app.queue.producer import publish_resume_job
from app.core.security import decode_token
from app.core.file_validation import validate_file, sanitize_filename, is_safe_filename, FileValidationError
from app.core.s3_storage import upload_to_s3, is_s3_configured, S3StorageError
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
    """Verify JWT token and return user payload"""
    token = credentials.credentials
    
    if not token or token in ["null", "undefined", "None"]:
        logger.warning("Invalid token format received")
        raise AuthenticationError("Invalid token format")
    
    try:
        payload = decode_token(token)
        if "sub" not in payload:
            logger.warning("Token missing 'sub' claim")
            raise AuthenticationError("Invalid token payload: missing subject")
        return payload
    except ExpiredSignatureError:
        logger.warning("Expired token received")
        raise AuthenticationError("Token has expired. Please login again.")
    except JWTError:
        raise AuthenticationError("Invalid authentication credentials")
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
    """Upload resumes for a job - with file validation and optional S3 storage"""
    
    # Check job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check S3 availability
    use_s3 = is_s3_configured()
    if use_s3:
        logger.info("S3 storage enabled - files will be stored in cloud")
    else:
        logger.info("S3 not configured - using local storage")
    
    results = []
    for file in files:
        try:
            # Validate filename
            if not is_safe_filename(file.filename):
                raise HTTPException(status_code=400, detail=f"Invalid filename: {file.filename}")
            
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            
            # Read file content
            content = await file.read()
            
            # Validate file type and size
            is_valid, error_msg = validate_file(content, safe_filename)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            resume_id = str(uuid.uuid4())
            
            # Upload to S3 or local storage
            if use_s3:
                try:
                    s3_uri = upload_to_s3(content, safe_filename)
                    file_path = s3_uri  # Store S3 URI
                except S3StorageError as e:
                    logger.error(f"S3 upload failed: {e}, falling back to local storage")
                    use_s3 = False
                    # Continue with local storage
                else:
                    # Store S3 URI in database
                    pass
            else:
                # Local storage
                save_dir = "/tmp/resumes"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"{resume_id}.pdf")
                with open(save_path, "wb") as f:
                    f.write(content)
                file_path = save_path
            
            # Create resume record
            resume = Resume(
                id=resume_id,
                job_id=job_id,
                filename=safe_filename,
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
                "file_path": file_path,
                "job_description": job.description,
                "use_s3": use_s3,
            })
            
            results.append({
                "resume_id": resume_id, 
                "filename": safe_filename, 
                "status": "queued"
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {"uploaded": len([r for r in results if r.get("status") == "queued"]), "resumes": results}


@router.get("/results/{job_id}")
def get_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get screening results for a job"""
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
    """Direct screening endpoint — creates a temp job and queues resumes"""
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
    
    use_s3 = is_s3_configured()
    queued = []
    
    for file in resumes:
        try:
            # Validate filename
            if not is_safe_filename(file.filename):
                continue
            
            safe_filename = sanitize_filename(file.filename)
            content = await file.read()
            
            # Validate file
            is_valid, error_msg = validate_file(content, safe_filename)
            if not is_valid:
                continue
            
            resume_id = str(uuid.uuid4())
            
            # Store file
            if use_s3:
                try:
                    s3_uri = upload_to_s3(content, safe_filename)
                    file_path = s3_uri
                except S3StorageError:
                    use_s3 = False
                    save_path = f"/tmp/resumes/{resume_id}.pdf"
                    os.makedirs("/tmp/resumes", exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(content)
                    file_path = save_path
            else:
                save_path = f"/tmp/resumes/{resume_id}.pdf"
                os.makedirs("/tmp/resumes", exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(content)
                file_path = save_path
            
            resume = Resume(
                id=resume_id,
                job_id=job_id,
                filename=safe_filename,
                candidate_name_encrypted=encrypt("Unknown"),
                candidate_email_encrypted=encrypt("unknown@unknown.com"),
                status=ResumeStatus.queued,
            )
            db.add(resume)
            db.commit()
            
            publish_resume_job({
                "resume_id": resume_id,
                "job_id": job_id,
                "file_path": file_path,
                "job_description": job_description,
                "use_s3": use_s3,
            })
            
            queued.append({"resume_id": resume_id, "filename": safe_filename})
            
        except Exception as e:
            logger.error(f"Failed to queue {file.filename}: {e}")
    
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