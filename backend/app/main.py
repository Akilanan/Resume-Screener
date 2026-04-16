from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
from app.api.v1 import auth, jobs, resumes, admin, analytics
from app.core.logging import setup_logging
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, UserRole
from app.core.security import hash_password
from app.core.encryption import encrypt
import asyncio
import json
import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    
    # Setup Redis for WebSocket updates
    from app.core.config import settings
    app.state.redis = redis.Redis(host=settings.REDIS_HOST, port=6379, decode_responses=True)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == 'admin@talentai.com').first()
        if not user:
            admin = User(
                email='admin@talentai.com',
                name_encrypted=encrypt('Admin User'),
                hashed_password=hash_password('Admin@123'),
                role=UserRole.admin,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Admin user created: admin@talentai.com / Admin@123")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin: {e}")
    finally:
        db.close()
    
    yield


app = FastAPI(title="TalentAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/auth/test")
def test_auth():
    return {"message": "Backend is running"}


@app.get("/api/v1/debug/env")
def debug_env():
    from app.core.config import settings
    return {
        "llm_key_set": bool(settings.LLM_API_KEY),
        "redis_host": settings.REDIS_HOST,
        "rabbitmq_host": settings.RABBITMQ_HOST,
        "database_url_set": bool(settings.DATABASE_URL),
    }


# WebSocket endpoint for real-time screening updates
@app.websocket("/ws/screening/{job_id}")
async def websocket_screening(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        redis_client = websocket.app.state.redis
        channel = f"screening:{job_id}"
        
        # Subscribe to the Redis channel for this job
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        
        # Send initial connection message
        await websocket.send_json({"status": "connected", "job_id": job_id})
        
        # Listen for messages and forward to WebSocket
        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
                
                # Close connection when screening is complete
                if data.get("status") == "complete":
                    break
                    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Endpoint to trigger progress updates (called by worker)
@app.post("/api/v1/screening/progress")
async def update_screening_progress(job_id: str, resume_id: str, status: str, score: float = None):
    """Called by worker to update progress - publishes to Redis channel"""
    redis_client = app.state.redis
    channel = f"screening:{job_id}"
    
    data = {
        "status": status,
        "resume_id": resume_id,
        "score": score,
    }
    await redis_client.publish(channel, json.dumps(data))
    return {"status": "ok"}
