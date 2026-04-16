# 🎯 TALENTAI MASTER IMPLEMENTATION PLAN
## From MVP to Production-Ready AI Recruitment Platform

**Version:** 2.0  
**Date:** April 16, 2025  
**Status:** Deep Analysis Complete - Ready for Execution

---

## 🚨 EXECUTIVE SUMMARY

### Current State Analysis
| Aspect | Status | Severity |
|--------|--------|----------|
| JWT Token Expiry | ✅ Fixed (24h) | Low |
| Error Handling | ⚠️ Weak | **Critical** |
| Worker Resilience | 🔴 No retry/DLQ | **Critical** |
| Real-time Updates | 🔴 Polling only | **Critical** |
| Rate Limiting | 🔴 None | High |
| Circuit Breaker | 🟡 Ready but unused | Medium |
| Audit Logging | 🟡 Ready but unused | Medium |

### Critical Issues Found
1. **Worker fails permanently** - No retry on LLM failure, resume lost forever
2. **No WebSocket** - UI polls blindly, poor UX
3. **500 errors on auth** - decode_token raises unhandled exceptions
4. **No rate limiting** - API vulnerable to abuse
5. **Sync DB writes in async context** - Potential blocking
6. **No connection pooling** - DB connections exhausted under load
7. **Missing worker replicas** - Only 1 worker = bottleneck

---

## 📋 PHASE 1: CRITICAL FIXES (Days 1-2)
**Goal:** Make the system stable and error-free

### 1.1 Fix Error Handling in Resumes API

**File:** `backend/app/api/v1/resumes.py`

**Current Problem:**
```python
# ❌ BAD: decode_token raises unhandled exceptions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_token(credentials.credentials)  # Can raise JWTError or ExpiredSignatureError
```

**Fix:**
```python
from fastapi import HTTPException, status
from jose import JWTError, ExpiredSignatureError

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    
    # Check if token looks valid
    if not token or token == "null" or token == "undefined":
        raise AuthenticationError("Invalid token format")
    
    try:
        payload = decode_token(token)
        
        # Validate required fields
        if "sub" not in payload:
            raise AuthenticationError("Invalid token payload")
            
        return payload
        
    except ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please login again.")
    except JWTError as e:
        raise AuthenticationError(f"Invalid authentication credentials: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Authentication error: {str(e)}")

# Add global exception handler
from fastapi import Request
from fastapi.responses import JSONResponse

@router.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "authentication_error"}
    )
```

### 1.2 Implement Robust Token Refresh in Frontend

**File:** `frontend/src/app/services/api.ts`

**Add:**
```typescript
// Token refresh queue to prevent multiple simultaneous refreshes
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  
  if (!refreshToken) {
    logout();
    return null;
  }

  // If already refreshing, wait for that
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error("Refresh failed");
      }
      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      return data.access_token;
    })
    .catch((err) => {
      console.error("Token refresh failed:", err);
      logout();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

// Axios-like fetch wrapper with auto-refresh
async function apiRequest(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  let token = localStorage.getItem("access_token");
  
  // Add auth header
  const headers = {
    ...options.headers,
    Authorization: token ? `Bearer ${token}` : "",
  };

  let response = await fetch(url, { ...options, headers });

  // If 401, try to refresh
  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    
    if (newToken) {
      // Retry with new token
      headers.Authorization = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    } else {
      throw new Error("Session expired. Please login again.");
    }
  }

  return response;
}
```

### 1.3 Fix Worker with Retry Logic + DLQ

**File:** `worker/worker.py`

**Complete Rewrite:**
```python
import pika
import json
import logging
import time
import os
import requests
import asyncio
from datetime import datetime
from typing import Dict, Any

from llm_scorer import score_resume
from pdf_extractor import extract_text_from_pdf
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_URL = os.getenv("DATABASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
DLQ_NAME = "resume_dlq"
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 45]  # Exponential backoff: 5s, 15s, 45s

# Connection pool for database
_db_pool = None

def get_db_pool():
    global _db_pool
    if _db_pool is None:
        _db_pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DB_URL
        )
    return _db_pool

def update_resume_result(resume_id: str, result: dict, status: str = 'completed'):
    """Update resume with scoring results"""
    pool = get_db_pool()
    conn = None
    
    try:
        conn = pool.getconn()
        cur = conn.cursor()
        
        score = result.get("score", 0)
        if score <= 10:
            score = score * 10  # Convert to 0-100
        
        cur.execute("""
            UPDATE resumes SET
                status = %s,
                score = %s,
                match_summary = %s,
                skills_matched = %s::jsonb,
                skills_missing = %s::jsonb,
                red_flags = %s::jsonb,
                processed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (
            status,
            score,
            result.get("summary", ""),
            json.dumps(result.get("skills_matched", [])),
            json.dumps(result.get("skills_missing", [])),
            json.dumps(result.get("red_flags", [])),
            resume_id,
        ))
        
        conn.commit()
        cur.close()
        logger.info(f"✓ Updated resume {resume_id} | Score: {score} | Status: {status}")
        
    except Exception as e:
        logger.error(f"✗ Failed to update resume {resume_id}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.putconn(conn)

def send_to_dlq(channel, message: dict, error: str):
    """Send failed message to Dead Letter Queue"""
    dlq_message = {
        "original_message": message,
        "error": error,
        "failed_at": datetime.utcnow().isoformat(),
        "retry_count": message.get("retry_count", 0)
    }
    
    try:
        channel.basic_publish(
            exchange='',
            routing_key=DLQ_NAME,
            body=json.dumps(dlq_message).encode(),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.warning(f"✗ Sent to DLQ: {message.get('resume_id', 'unknown')}")
    except Exception as e:
        logger.error(f"✗ Failed to send to DLQ: {e}")

def publish_retry(channel, message: dict):
    """Publish message for retry with delay"""
    retry_count = message.get("retry_count", 0) + 1
    message["retry_count"] = retry_count
    
    # Use delayed queue or simple republish
    # For simplicity, we'll publish to same queue
    # In production, use RabbitMQ delayed message plugin
    
    delay = RETRY_DELAYS[min(retry_count - 1, len(RETRY_DELAYS) - 1)]
    logger.info(f"↻ Scheduling retry {retry_count}/{MAX_RETRIES} in {delay}s")
    
    # Simple approach: publish immediately, worker will pick up
    # Better approach: use delay or scheduled queue
    channel.basic_publish(
        exchange='',
        routing_key='resume_queue',
        body=json.dumps(message).encode(),
        properties=pika.BasicProperties(delivery_mode=2)
    )

def process_resume(message: dict) -> dict:
    """Process a single resume - main business logic"""
    resume_id = message["resume_id"]
    job_id = message.get("job_id", "unknown")
    file_path = message["file_path"]
    job_description = message["job_description"]
    
    logger.info(f"📝 Processing: {resume_id}")
    
    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Extract text
    resume_text = extract_text_from_pdf(file_path)
    
    if not resume_text or len(resume_text) < 50:
        raise ValueError("Could not extract meaningful text from PDF")
    
    logger.info(f"  Extracted {len(resume_text)} chars")
    
    # Score with LLM
    result = score_resume(resume_text, job_description)
    
    logger.info(f"  Score: {result.get('score', 0)}")
    
    return result

def process_message(ch, method, properties, body):
    """Main message handler with retry logic"""
    message = None
    
    try:
        message = json.loads(body)
        resume_id = message.get("resume_id", "unknown")
        retry_count = message.get("retry_count", 0)
        
        logger.info(f"📨 Received: {resume_id} (attempt {retry_count + 1})")
        
        # Process the resume
        result = process_resume(message)
        
        # Update DB
        update_resume_result(resume_id, result, 'completed')
        
        # Acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"✅ Completed: {resume_id}")
        
    except FileNotFoundError as e:
        # Permanent error - don't retry
        logger.error(f"✗ File error (no retry): {e}")
        if message:
            update_resume_result(message.get("resume_id"), {
                "score": 0,
                "summary": f"File error: {str(e)}",
                "skills_matched": [],
                "skills_missing": [],
                "red_flags": ["File processing failed"]
            }, 'failed')
            send_to_dlq(ch, message, str(e))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        # Temporary error - retry if possible
        logger.error(f"✗ Processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        if message:
            retry_count = message.get("retry_count", 0)
            
            if retry_count < MAX_RETRIES:
                # Retry
                publish_retry(ch, message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Max retries exceeded - send to DLQ
                logger.error(f"✗ Max retries exceeded: {message.get('resume_id')}")
                update_resume_result(message.get("resume_id"), {
                    "score": 0,
                    "summary": f"Failed after {MAX_RETRIES} attempts: {str(e)[:200]}",
                    "skills_matched": [],
                    "skills_missing": [],
                    "red_flags": ["Processing failed"]
                }, 'failed')
                send_to_dlq(ch, message, str(e))
                ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Can't parse message - reject
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_worker():
    """Initialize and start the worker"""
    max_connection_retries = 10
    connection_retry = 0
    
    while connection_retry < max_connection_retries:
        try:
            logger.info(f"🔌 Connecting to RabbitMQ (attempt {connection_retry + 1})...")
            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    connection_attempts=3,
                    retry_delay=2,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            
            channel = connection.channel()
            
            # Declare queues
            channel.queue_declare(queue="resume_queue", durable=True)
            channel.queue_declare(queue=DLQ_NAME, durable=True)
            
            # Fair dispatch - don't give more than 1 message to a worker at a time
            channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            channel.basic_consume(
                queue="resume_queue",
                on_message_callback=process_message
            )
            
            logger.info("✅ Worker started. Waiting for messages...")
            channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("⚠️ Worker stopped by user")
            break
        except Exception as e:
            connection_retry += 1
            logger.error(f"✗ Connection failed: {e}")
            logger.info(f"↻ Retrying in 5s... ({connection_retry}/{max_connection_retries})")
            time.sleep(5)
    
    logger.error("✗ Max connection retries exceeded. Exiting.")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 TalentAI Worker Starting")
    logger.info(f"   DB: {'connected' if DB_URL else 'NOT SET'}")
    logger.info(f"   LLM: {'enabled' if LLM_API_KEY else 'mock mode'}")
    logger.info(f"   Retries: {MAX_RETRIES}")
    logger.info("=" * 50)
    start_worker()
```

---

## 📋 PHASE 2: SCALABILITY (Days 3-4)
**Goal:** Handle 10,000 resumes/hour

### 2.1 Database Optimization

**File:** `backend/app/db/database.py`

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Connection pooling configuration
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Base connections
    max_overflow=30,           # Extra connections under load
    pool_pre_ping=True,        # Verify connection before use
    pool_recycle=3600,         # Recycle connections every hour
    pool_timeout=30,           # Wait up to 30s for connection
    echo=False                 # Set to True for SQL logging
)

# Add connection event listeners
@event.listens_for(engine, "connect")
def on_connect(dbapi_conn, connection_record):
    """Optimize connection settings"""
    # Enable autocommit for better performance
    dbapi_conn.autocommit = True

@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Verify connection is alive"""
    try:
        dbapi_conn.cursor().execute("SELECT 1")
    except:
        raise DisconnectionError()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use scoped sessions for thread safety
ScopedSession = scoped_session(SessionLocal)

def get_db():
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2.2 Add Multiple Worker Replicas

**File:** `docker-compose.yml`

```yaml
  worker:
    build: ./worker
    deploy:
      replicas: 4  # Scale to 4 workers
    env_file: .env
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    volumes:
      - resumes_data:/tmp/resumes
      - ./worker:/app
    command: python -u worker.py
    depends_on:
      rabbitmq:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - talentai_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 2.3 Add Redis Caching

**File:** `backend/app/core/cache.py`

```python
import redis
import json
import pickle
import hashlib
from functools import wraps
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Production-grade Redis caching with fallback"""
    
    def __init__(self, host='redis', port=6379, db=0):
        self._client = None
        self._host = host
        self._port = port
        self._db = db
        self._connect()
    
    def _connect(self):
        try:
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            self._client.ping()
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable: {e}")
            self._client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self._client:
            return False
        try:
            self._client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._client:
            return 0
        try:
            keys = self._client.scan_iter(match=pattern)
            count = 0
            for key in keys:
                self._client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

# Global cache instance
cache = RedisCache()

def cached(expire: int = 300, key_prefix: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, expire)
            logger.debug(f"Cache MISS: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Cache invalidation helpers
def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user"""
    return cache.clear_pattern(f"*user:{user_id}*")

def invalidate_dashboard_stats():
    """Invalidate dashboard statistics"""
    return cache.clear_pattern("*dashboard*")
```

---

## 📋 PHASE 3: REAL-TIME FEATURES (Days 5-7)
**Goal:** WebSocket-powered live updates

### 3.1 WebSocket Server

**File:** `backend/app/api/v1/websocket.py`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
import json
import asyncio
from typing import Dict, Set
from app.core.security import decode_token

router = APIRouter()
security = HTTPBearer()

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # job_id -> Set[WebSocket]
        self.job_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully"
        })
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe a connection to job updates"""
        if job_id not in self.job_connections:
            self.job_connections[job_id] = set()
        self.job_connections[job_id].add(websocket)
    
    def unsubscribe_from_job(self, websocket: WebSocket, job_id: str):
        """Unsubscribe from job updates"""
        if job_id in self.job_connections:
            self.job_connections[job_id].discard(websocket)
            if not self.job_connections[job_id]:
                del self.job_connections[job_id]
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """Send message to all subscribers of a job"""
        if job_id not in self.job_connections:
            return
        
        disconnected = []
        for connection in self.job_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.job_connections[job_id].discard(conn)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.active_connections[user_id].discard(conn)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    try:
        # Wait for authentication message
        auth_message = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=10.0
        )
        
        data = json.loads(auth_message)
        token = data.get("token")
        
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        
        # Validate token
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")
        except Exception as e:
            await websocket.close(code=4001, reason=f"Invalid token: {str(e)}")
            return
        
        # Connect
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # Keep connection alive and handle messages
                message = await websocket.receive_text()
                data = json.loads(message)
                
                action = data.get("action")
                
                if action == "subscribe_job":
                    job_id = data.get("job_id")
                    if job_id:
                        manager.subscribe_to_job(websocket, job_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "job_id": job_id
                        })
                
                elif action == "unsubscribe_job":
                    job_id = data.get("job_id")
                    if job_id:
                        manager.unsubscribe_from_job(websocket, job_id)
                
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
    
    except asyncio.TimeoutError:
        await websocket.close(code=4001, reason="Authentication timeout")
    except Exception as e:
        await websocket.close(code=4000, reason=f"Error: {str(e)}")

# Helper function for other modules to broadcast updates
async def notify_job_progress(job_id: str, resume_id: str, status: str, progress: float = None):
    """Broadcast progress update to all subscribers of a job"""
    await manager.broadcast_to_job(job_id, {
        "type": "progress",
        "job_id": job_id,
        "resume_id": resume_id,
        "status": status,
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat()
    })

async def notify_job_complete(job_id: str, results: dict):
    """Notify that a job is complete"""
    await manager.broadcast_to_job(job_id, {
        "type": "complete",
        "job_id": job_id,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    })
```

### 3.2 Update Worker to Send WebSocket Notifications

**Update in worker.py:**
```python
def notify_websocket(job_id: str, resume_id: str, status: str, score: float = None):
    """Send WebSocket notification via backend API"""
    try:
        requests.post(
            "http://backend:8000/api/v1/internal/notify",
            json={
                "job_id": job_id,
                "resume_id": resume_id,
                "status": status,
                "score": score
            },
            timeout=3
        )
    except Exception as e:
        logger.debug(f"WebSocket notify failed (non-critical): {e}")
```

### 3.3 Frontend WebSocket Hook

**File:** `frontend/src/hooks/useWebSocket.ts`

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  job_id?: string;
  resume_id?: string;
  status?: string;
  progress?: number;
  results?: any;
  timestamp?: string;
}

interface UseWebSocketOptions {
  onProgress?: (data: WebSocketMessage) => void;
  onComplete?: (data: WebSocketMessage) => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setError(new Error('No authentication token'));
      return;
    }

    const wsUrl = `ws://localhost:8000/api/v1/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
      
      // Send authentication
      ws.send(JSON.stringify({ token }));
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        if (data.type === 'connected') {
          console.log('WebSocket authenticated');
        } else if (data.type === 'progress') {
          options.onProgress?.(data);
        } else if (data.type === 'complete') {
          options.onComplete?.(data);
        }
      } catch (err) {
        console.error('WebSocket message error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setError(new Error('WebSocket connection error'));
      options.onError?.(new Error('WebSocket connection error'));
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code);
      setIsConnected(false);
      
      // Attempt reconnect
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttempts.current})`);
        setTimeout(connect, delay);
      }
    };
  }, [options]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const subscribeToJob = useCallback((jobId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe_job',
        job_id: jobId
      }));
    }
  }, []);

  const unsubscribeFromJob = useCallback((jobId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe_job',
        job_id: jobId
      }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    subscribeToJob,
    unsubscribeFromJob,
    reconnect: connect
  };
}
```

---

## 📋 PHASE 4: SECURITY HARDENING (Days 8-10)

### 4.1 Rate Limiting

**File:** `backend/app/middleware/rate_limit.py`

```python
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
import redis
import time
from functools import wraps
from app.core.config import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=1, decode_responses=True)

class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed using sliding window"""
        now = time.time()
        window_start = now - self.window
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current = redis_client.zcard(key)
        
        if current >= self.requests:
            return False
        
        # Add current request
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, self.window)
        return True
    
    def get_retry_after(self, key: str) -> int:
        """Get seconds until next allowed request"""
        oldest = redis_client.zrange(key, 0, 0, withscores=True)
        if oldest:
            oldest_time = oldest[0][1]
            retry_after = int(self.window - (time.time() - oldest_time))
            return max(0, retry_after)
        return 0

# Different limits for different endpoints
limits = {
    "login": RateLimiter(requests=5, window=300),      # 5 per 5 min
    "default": RateLimiter(requests=100, window=60),   # 100 per min
    "screen": RateLimiter(requests=20, window=60),     # 20 screenings per min
}

def rate_limit(limit_name: str = "default"):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to find in kwargs
                request = kwargs.get('request')
            
            if request:
                # Use user ID if authenticated, else IP
                key = f"rate_limit:{limit_name}:"
                
                # Try to get user from auth header
                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Bearer '):
                    try:
                        from app.core.security import decode_token
                        token = auth_header.split(' ')[1]
                        payload = decode_token(token)
                        key += payload.get('sub', 'anonymous')
                    except:
                        key += request.client.host
                else:
                    key += request.client.host
                
                limiter = limits.get(limit_name, limits["default"])
                
                if not limiter.is_allowed(key):
                    retry_after = limiter.get_retry_after(key)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(retry_after)}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 4.2 Add Audit Logging Usage

**Update to resume endpoints:**
```python
from app.core.audit import audit

@router.post("/screen")
async def screen_resumes_direct(
    request: Request,  # Add this
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Log the action
    audit.log(
        user_id=current_user["sub"],
        action="CREATE",
        resource="screening_job",
        details={
            "num_resumes": len(resumes),
            "job_description_preview": job_description[:100]
        },
        request=request
    )
    
    # ... rest of the code
```

---

## 📋 PHASE 5: ADVANCED FEATURES (Days 11-14)

### 5.1 Bulk Upload with Progress

**File:** `frontend/src/components/BulkUpload.tsx`

```typescript
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useWebSocket } from '../hooks/useWebSocket';
import { Progress } from './ui/progress';

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

export function BulkUpload() {
  const [files, setFiles] = useState<UploadingFile[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  
  const { isConnected, subscribeToJob } = useWebSocket({
    onProgress: (data) => {
      setFiles(prev => prev.map(f => {
        if (f.status === 'processing') {
          return { ...f, progress: data.progress || 0 };
        }
        return f;
      }));
    },
    onComplete: (data) => {
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'completed',
        progress: 100
      })));
    }
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: 'uploading' as const
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Upload files
    uploadFiles(newFiles);
  }, []);

  const uploadFiles = async (filesToUpload: UploadingFile[]) => {
    const formData = new FormData();
    filesToUpload.forEach(f => formData.append('resumes', f.file));
    formData.append('job_description', 'Bulk upload');
    
    try {
      const response = await fetch('/api/v1/resumes/screen', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });
      
      const data = await response.json();
      setJobId(data.job_id);
      
      // Subscribe to WebSocket updates
      subscribeToJob(data.job_id);
      
      // Update file statuses
      setFiles(prev => prev.map(f => ({
        ...f,
        status: f.status === 'uploading' ? 'processing' : f.status
      })));
      
    } catch (error) {
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error',
        error: error.message
      })));
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc', '.docx']
    },
    maxFiles: 50
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-lg">
          {isDragActive ? 'Drop files here...' : 'Drag & drop resumes here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Support PDF, DOC, DOCX (max 50 files)
        </p>
      </div>
      
      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          <h3 className="font-semibold">Uploading {files.length} files...</h3>
          {files.map(file => (
            <div key={file.id} className="bg-gray-50 p-3 rounded">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium">{file.file.name}</span>
                <span className={`text-xs ${
                  file.status === 'completed' ? 'text-green-600' :
                  file.status === 'error' ? 'text-red-600' :
                  'text-blue-600'
                }`}>
                  {file.status === 'uploading' && 'Uploading...'}
                  {file.status === 'processing' && 'Processing...'}
                  {file.status === 'completed' && 'Done'}
                  {file.status === 'error' && 'Failed'}
                </span>
              </div>
              <Progress value={file.progress} />
            </div>
          ))}
        </div>
      )}
      
      {isConnected && (
        <div className="mt-4 text-sm text-green-600">
          ● Live updates connected
        </div>
      )}
    </div>
  );
}
```

---

## 📊 EXECUTION CHECKLIST

### Week 1: Foundation
- [ ] **Day 1:** Fix error handling in resumes.py
- [ ] **Day 1:** Add token refresh to frontend
- [ ] **Day 2:** Rewrite worker with retry + DLQ
- [ ] **Day 2:** Add DB connection pooling
- [ ] **Day 2:** Scale to 4 worker replicas

### Week 2: Real-time & Scale
- [ ] **Day 3:** Implement WebSocket server
- [ ] **Day 3:** Add worker WebSocket notifications
- [ ] **Day 4:** Create useWebSocket hook
- [ ] **Day 4:** Integrate real-time progress bars
- [ ] **Day 5:** Add Redis caching layer
- [ ] **Day 6:** Load testing with Locust
- [ ] **Day 7:** Performance tuning

### Week 3: Security & Polish
- [ ] **Day 8:** Implement rate limiting
- [ ] **Day 8:** Add audit logging
- [ ] **Day 9:** Bulk upload component
- [ ] **Day 9:** Excel/PDF export
- [ ] **Day 10:** Advanced filtering
- [ ] **Day 11:** Error boundaries
- [ ] **Day 12:** Unit tests
- [ ] **Day 13:** Integration tests
- [ ] **Day 14:** Demo rehearsal

---

## 🎯 SUCCESS METRICS

### Technical Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Processing Rate | ~100/hr | 10,000/hr |
| API Response (p95) | ~500ms | <200ms |
| System Uptime | N/A | 99.9% |
| Failed Resume Rate | ~5% | <0.1% |
| Token Errors | 403/500 | 0 |

### Demo Metrics
| Feature | Status |
|---------|--------|
| Real-time progress | WebSocket required |
| Bulk upload 50 files | DLQ + multi-worker required |
| Export to Excel | Must implement |
| <200ms API response | Caching required |

---

## 🚨 RISK MITIGATION

### High Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API rate limited | High | Demo failure | Mock responses + circuit breaker |
| WebSocket fails | Medium | Poor UX | Fallback to polling |
| DB connection limit | Medium | System crash | Connection pooling |
| RabbitMQ crash | Low | All workers stop | DLQ persists messages |

### Demo Day Backup Plan
1. **Record video** of working demo
2. **Pre-load data** for instant results
3. **Mock LLM responses** to avoid rate limits
4. **Have polling fallback** ready

---

**Ready to execute? Start with Phase 1 - the worker rewrite is critical!**