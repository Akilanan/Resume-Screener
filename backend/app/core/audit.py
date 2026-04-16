"""
Audit Logging System
Tracks all sensitive operations for compliance and security
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, JSON, Integer
import json
import logging

from app.db.database import Base, SessionLocal

logger = logging.getLogger("audit")


class AuditLog(Base):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, index=True)
    action = Column(String, index=True)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT
    resource = Column(String)  # resumes, jobs, users, etc.
    resource_id = Column(String, nullable=True)
    ip_address = Column(String)
    user_agent = Column(String)
    details = Column(JSON)  # Flexible JSON for additional context
    success = Column(String, default="true")  # true/false


class AuditLogger:
    """
    Centralized audit logging
    
    Usage:
        from app.core.audit import audit
        
        @router.get("/admin/resumes")
        def get_resumes(current_user: User = Depends(...), request: Request):
            audit.log(
                user_id=current_user.id,
                action="READ",
                resource="resumes",
                details={"filters": filters},  # type: ignore
                request=request
            )
            return get_resumes_from_db()
    """
    
    def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        request=None,
        success: bool = True,
        resource_id: Optional[str] = None
    ):
        """Create an audit log entry"""
        
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = getattr(request.client, "host", None)
            user_agent = request.headers.get("user-agent")
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "success": "true" if success else "false"
        }
        
        # Log to file immediately
        logger.info(json.dumps(log_entry))
        
        # Try to save to database (async fire-and-forget)
        try:
            db = SessionLocal()
            audit = AuditLog(**log_entry)
            db.add(audit)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to write audit log to DB: {e}")
    
    def log_login(self, user_id: str, success: bool, request=None, details=None):
        """Convenience method for login events"""
        self.log(
            user_id=user_id,
            action="LOGIN",
            resource="auth",
            details=details or {},
            request=request,
            success=success
        )
    
    def log_resume_access(self, user_id: str, resume_id: str, action: str, request=None):
        """Convenience method for resume access events"""
        self.log(
            user_id=user_id,
            action=action,
            resource="resumes",
            resource_id=resume_id,
            details={},
            request=request,
            success=True
        )


# Global instance
audit = AuditLogger()
