from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
from pydantic import BaseModel
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


@app.get("/api/v1/health/detailed")
def detailed_health():
    """Comprehensive health check for all services"""
    results = {
        "status": "ok",
        "services": {}
    }
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        from app.db.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        results["services"]["postgres"] = {"status": "healthy"}
    except Exception as e:
        results["services"]["postgres"] = {"status": "unhealthy", "error": str(e)}
        results["status"] = "degraded"
    
    # Check Redis
    try:
        r = redis.Redis(host='redis', port=6379)
        r.ping()
        results["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        results["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        results["status"] = "degraded"
    
    # Check RabbitMQ
    try:
        import pika
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
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
        
        # Use pubsub for real-time updates
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        
        # Send initial connection message
        await websocket.send_json({"status": "connected", "job_id": job_id})
        
        # Listen for messages in a loop
        while True:
            try:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                    
                    # Close connection when screening is complete
                    if data.get("status") == "complete":
                        break
            except Exception as e:
                print(f"WebSocket message error: {e}")
                break
                    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
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

@app.post("/api/v1/screening/progress")
async def update_screening_progress(request: ScreeningProgressRequest):
    """Called by worker to update progress - publishes to Redis channel"""
    try:
        redis_client = app.state.redis
        channel = f"screening:{request.job_id}"
        
        data = {
            "status": request.status,
            "resume_id": request.resume_id,
            "score": request.score,
        }
        redis_client.publish(channel, json.dumps(data))
        return {"status": "ok"}
    except Exception as e:
        print(f"Error publishing progress: {e}")
        return {"status": "error", "message": str(e)}
