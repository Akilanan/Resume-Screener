from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
from pydantic import BaseModel
from app.api.v1 import auth, jobs, resumes, admin, analytics
from app.core.logging import setup_logging
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, UserRole
from app.core.security import hash_password
from app.core.encryption import encrypt
from app.core.config import settings
import json
import redis
import logging

logger = logging.getLogger(__name__)


def create_initial_admin():
    """Create admin user from environment variables - NOT hardcoded"""
    db = SessionLocal()
    try:
        # Check if admin email is provided via environment
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD
        
        if not admin_email or not admin_password:
            logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD not set. No admin user will be created.")
            logger.warning("Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables for initial deployment.")
            return
        
        # Check if admin already exists
        user = db.query(User).filter(User.email == admin_email).first()
        if user:
            logger.info(f"Admin user {admin_email} already exists")
            return
        
        # Create admin user
        admin = User(
            email=admin_email,
            name_encrypted=encrypt('Admin User'),
            hashed_password=hash_password(admin_password),
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin)
        db.commit()
        logger.info(f"Admin user created: {admin_email}")
        
    except Exception as e:
        logger.error(f"Error creating admin: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    
    # Setup Redis for WebSocket updates
    app.state.redis = redis.Redis(
        host=settings.REDIS_HOST, 
        port=6379, 
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    # Create admin from environment variables
    create_initial_admin()
    
    yield


app = FastAPI(
    title="TalentAI API", 
    version="1.0.0", 
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"] if settings.LLM_API_KEY else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    import uuid
    
    # Add request ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"[{request_id}] Error processing {request.method} {request.url.path}: {str(e)}")
        raise
    process_time = time.time() - start_time
    logger.debug(f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__}
    )


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/")
def root():
    """Root endpoint - redirect to API documentation"""
    return {
        "message": "TalentAI Backend API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health",
        "frontend_url": "http://localhost:5173"
    }


@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/health/detailed")
def detailed_health():
    """Comprehensive health check for all services"""
    results = {"status": "ok", "services": {}}
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        results["services"]["postgres"] = {"status": "healthy"}
    except Exception as e:
        results["services"]["postgres"] = {"status": "unhealthy", "error": str(e)}
        results["status"] = "degraded"
    
    # Check Redis
    try:
        r = redis.Redis(host='redis', port=6379, socket_connect_timeout=3)
        r.ping()
        results["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        results["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        results["status"] = "degraded"
    
    # Check RabbitMQ
    try:
        import pika
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', connection_attempts=3, retry_delay=1))
        connection.close()
        results["services"]["rabbitmq"] = {"status": "healthy"}
    except Exception as e:
        results["services"]["rabbitmq"] = {"status": "unhealthy", "error": str(e)}
        results["status"] = "degraded"
    
    return results


@app.get("/api/v1/auth/test")
def test_auth():
    return {"message": "Backend is running"}


@app.get("/api/v1/debug/env")
def debug_env():
    return {
        "llm_key_set": bool(settings.LLM_API_KEY),
        "redis_host": settings.REDIS_HOST,
        "rabbitmq_host": settings.RABBITMQ_HOST,
        "database_url_set": bool(settings.DATABASE_URL),
        "admin_email_set": bool(settings.ADMIN_EMAIL),
    }


# WebSocket endpoint for real-time screening updates
@app.websocket("/ws/screening/{job_id}")
async def websocket_screening(websocket: WebSocket, job_id: str):
    await websocket.accept()
    pubsub = None
    try:
        redis_client = websocket.app.state.redis
        channel = f"screening:{job_id}"
        
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        
        await websocket.send_json({"status": "connected", "job_id": job_id})
        
        while True:
            try:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                    
                    if data.get("status") == "complete":
                        break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if pubsub:
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
            except:
                pass
        await websocket.close()


# Endpoint to trigger progress updates (called by worker)
class ScreeningProgressRequest(BaseModel):
    job_id: str
    resume_id: str
    status: str
    score: float | None = None
    error: str | None = None

@app.post("/api/v1/screening/progress")
async def update_screening_progress(request: ScreeningProgressRequest):
    """Called by worker to update progress"""
    try:
        redis_client = app.state.redis
        channel = f"screening:{request.job_id}"
        
        data = {
            "status": request.status,
            "resume_id": request.resume_id,
            "score": request.score,
            "error": request.error,
        }
        redis_client.publish(channel, json.dumps(data))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error publishing progress: {e}")
        return {"status": "error", "message": str(e)}