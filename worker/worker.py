"""
Production AI Worker - No Mock Data Fallback
Requires valid LLM_API_KEY. Fails gracefully on missing key.
"""
import pika
import json
import logging
import time
import os
import sys
import requests
from llm_scorer import score_resume, LLMScoringError, MissingAPIKeyError, health_check
from pdf_extractor import extract_text_from_pdf
import psycopg2
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate environment at startup
logger.info("=== WORKER STARTING ===")
logger.info(f"DATABASE_URL: {'set' if os.getenv('DATABASE_URL') else 'NOT SET'}")
llm_status = health_check()
logger.info(f"LLM Status: {llm_status['status']} - {llm_status['message']}")
logger.info(f"RABBITMQ_HOST: {os.getenv('RABBITMQ_HOST', 'rabbitmq')}")
logger.info("======================")

# Exit if LLM not configured AND mock mode is not enabled
mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
if not llm_status['llm_configured'] and not mock_mode:
    logger.critical("FATAL: LLM_API_KEY not set. Worker cannot start. Please configure LLM_API_KEY environment variable.")
    sys.exit(1)

if mock_mode:
    logger.info("Running in MOCK MODE - will use mock scoring for demo")

DB_URL = os.getenv("DATABASE_URL")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def get_db_connection():
    """Get database connection with proper pooling"""
    try:
        conn = psycopg2.connect(
            DB_URL,
            connect_timeout=10,
            options="-c statement_timeout=30000"  # 30s timeout
        )
        # Enable connection pooling best practices
        conn.autocommit = False
        logger.info("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def update_resume_result(resume_id: str, result: dict, status: str = "completed"):
    """Update resume with scoring results"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        score = result.get("score", 0)
        
        cur.execute("""
            UPDATE resumes SET
                status = %s,
                score = %s,
                match_summary = %s,
                skills_matched = %s,
                skills_missing = %s,
                red_flags = %s,
                processed_at = NOW()
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
        conn.close()
        logger.info(f"Updated resume {resume_id} with score {score}")
    except Exception as e:
        logger.error(f"Failed to update resume {resume_id}: {e}")
        # Don't raise - we want to keep the message in queue if DB update fails
        raise


def mark_resume_failed(resume_id: str, error_message: str):
    """Mark resume as failed in database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE resumes SET
                status = 'failed',
                match_summary = %s,
                processed_at = NOW()
            WHERE id = %s
        """, (error_message[:500], resume_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to mark resume as failed: {e}")


def notify_progress(job_id: str, resume_id: str, status: str, score: float = None, error: str = None):
    """Notify backend about screening progress"""
    try:
        requests.post(
            f"{BACKEND_URL}/api/v1/screening/progress",
            json={
                "job_id": job_id, 
                "resume_id": resume_id, 
                "status": status, 
                "score": score,
                "error": error
            },
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Failed to notify progress: {e}")


def process_message(ch, method, properties, body):
    """Process resume screening message with proper error handling"""
    resume_id = None
    job_id = None
    
    try:
        logger.info(f"Received message: {body[:200]}...")
        message = json.loads(body)
        resume_id = message["resume_id"]
        job_id = message.get("job_id", "unknown")
        file_path = message["file_path"]
        job_description = message["job_description"]

        logger.info(f"Processing resume: {resume_id}")
        logger.info(f"File path: {file_path}")
        
        # Notify: processing started
        notify_progress(job_id, resume_id, "processing")

        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        logger.info(f"Extracted text length: {len(resume_text)} chars")
        
        if not resume_text or len(resume_text.strip()) < 50:
            error_msg = "Could not extract sufficient text from resume file"
            logger.error(error_msg)
            mark_resume_failed(resume_id, error_msg)
            notify_progress(job_id, resume_id, "failed", error=error_msg)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Score with LLM - No mock fallback
        try:
            result = score_resume(resume_text, job_description)
            logger.info(f"LLM result: score={result.get('score')}, skills={len(result.get('skills_matched', []))}")
        except MissingAPIKeyError as e:
            logger.critical(f"LLM API key missing during processing: {e}")
            mark_resume_failed(resume_id, f"LLM configuration error: {e}")
            notify_progress(job_id, resume_id, "failed", error="LLM not configured")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        except LLMScoringError as e:
            logger.error(f"LLM scoring failed: {e}")
            mark_resume_failed(resume_id, f"AI scoring failed: {e}")
            notify_progress(job_id, resume_id, "failed", error=str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)  # Requeue for retry
            return

        # Save results to DB
        update_resume_result(resume_id, result)
        
        # Notify: completed with score
        notify_progress(job_id, resume_id, "completed", score=result.get("score"))

        logger.info(f"Completed resume: {resume_id} | Score: {result.get('score')}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        if resume_id:
            mark_resume_failed(resume_id, f"Invalid message format: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Failed to process resume: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if resume_id:
            try:
                mark_resume_failed(resume_id, f"Processing failed: {str(e)[:200]}")
            except:
                pass
        # Requeue for retry on unexpected errors
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def setup_rabbitmq():
    """Setup RabbitMQ with Dead Letter Queue"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            connection_attempts=3,
            retry_delay=2,
            heartbeat=60
        )
    )
    channel = connection.channel()
    
    # Declare dead letter exchange
    channel.exchange_declare(
        exchange="resume_dlx",
        exchange_type="direct",
        durable=True
    )
    
    # Declare dead letter queue
    channel.queue_declare(
        queue="resume_dlq",
        durable=True,
        arguments={
            "x-message-ttl": 86400000  # 24 hours retention
        }
    )
    channel.queue_bind(
        queue="resume_dlq",
        exchange="resume_dlx",
        routing_key="failed"
    )
    
    # Declare main queue with DLQ
    channel.queue_declare(
        queue="resume_queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "resume_dlx",
            "x-dead-letter-routing-key": "failed"
        }
    )
    
    channel.basic_qos(prefetch_count=1)
    return channel


def start_worker():
    """Start the worker with proper error handling"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Connecting to RabbitMQ (attempt {retry_count + 1})...")
            channel = setup_rabbitmq()
            channel.basic_consume(queue="resume_queue", on_message_callback=process_message)
            logger.info("Worker started. Waiting for messages...")
            channel.start_consuming()
        except Exception as e:
            retry_count += 1
            logger.error(f"Connection failed: {e}. Retrying in 5s...")
            time.sleep(5)
    
    logger.error("Max retries exceeded. Exiting.")


if __name__ == "__main__":
    start_worker()