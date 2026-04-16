from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.database import get_db
from app.db.models import Resume, Job, ResumeStatus, JobStatus
from app.core.security import decode_token
from app.core.encryption import decrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from collections import Counter
from datetime import datetime, timezone

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_token(credentials.credentials)

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Basic Counts
    total_screened = db.query(Resume).count()
    avg_score = db.query(func.avg(Resume.score)).scalar() or 0
    shortlisted = db.query(Resume).filter(Resume.score >= 80).count()
    active_jobs = db.query(Job).filter(Job.status == JobStatus.open).count()

    # 2. Score Distribution
    # Ranges: 90-100, 80-89, 70-79, 60-69, <60
    ranges = [
        ("90-100%", 90, 101, "#7c3aed"),
        ("80-89%", 80, 90, "#8b5cf6"),
        ("70-79%", 70, 80, "#a78bfa"),
        ("60-69%", 60, 70, "#c4b5fd"),
        ("< 60%", 0, 60, "#ede9fe"),
    ]
    distribution = []
    for label, low, high, color in ranges:
        count = db.query(Resume).filter(Resume.score >= low, Resume.score < high).count()
        distribution.append({"name": label, "value": count, "fill": color})

    # 3. Recent Activity (Last 5)
    recent = db.query(Resume).order_by(desc(Resume.uploaded_at)).limit(5).all()
    activity = []
    for r in recent:
        # Attempt to decrypt name, or use filename
        name = "Unknown"
        try:
            if r.candidate_name_encrypted:
                name = decrypt(r.candidate_name_encrypted)
        except:
            name = r.filename.split(".")[0].replace("_", " ").title()
        
        # Calculate relative time string (simplified)
        now = datetime.now(timezone.utc)
        diff = now - r.uploaded_at
        if diff.days > 0:
            time_str = f"{diff.days}d ago"
        elif diff.seconds > 3600:
            time_str = f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            time_str = f"{diff.seconds // 60}m ago"
        else:
            time_str = "Just now"

        activity.append({
            "name": name,
            "score": int(r.score or 0),
            "job": r.job.title if r.job else "Quick Screen",
            "time": time_str,
            "status": "shortlisted" if (r.score or 0) >= 80 else "reviewing" if (r.score or 0) >= 60 else "rejected"
        })

    # 4. Top Skills
    all_skills = []
    completed_resumes = db.query(Resume.skills_matched).filter(Resume.status == ResumeStatus.completed).all()
    for (skills_json,) in completed_resumes:
        if skills_json:
            try:
                skills_list = json.loads(skills_json)
                all_skills.extend([s.strip() for s in skills_list if s])
            except:
                pass
    
    skill_counts = Counter(all_skills).most_common(6)
    skill_data = [{"skill": s, "count": c} for s, c in skill_counts]

    # Fallback if no skills yet
    if not skill_data:
        skill_data = [
            {"skill": "Python", "count": 0},
            {"skill": "React", "count": 0},
            {"skill": "AWS", "count": 0},
        ]

    return {
        "stats": {
            "total_screened": total_screened,
            "avg_match_score": round(float(avg_score), 1),
            "shortlisted": shortlisted,
            "active_jobs": active_jobs,
        },
        "score_distribution": distribution,
        "recent_activity": activity,
        "skill_data": skill_data
    }
