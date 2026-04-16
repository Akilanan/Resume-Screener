import pika
import json
import logging
import time
import os
import requests
from llm_scorer import score_resume
from pdf_extractor import extract_text_from_pdf
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log all environment variables at startup
logger.info("=== WORKER STARTING ===")
logger.info(f"DATABASE_URL: {'set' if os.getenv('DATABASE_URL') else 'NOT SET'}")
logger.info(f"LLM_API_KEY: {'set' if os.getenv('LLM_API_KEY') else 'NOT SET'}")
logger.info(f"RABBITMQ_HOST: {os.getenv('RABBITMQ_HOST', 'rabbitmq')}")
logger.info("======================")

DB_URL = os.getenv("DATABASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        logger.info("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def update_resume_result(resume_id: str, result: dict):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Handle score scaling (convert 0-10 to 0-100 if needed)
        score = result.get("score", 0)
        if score <= 10:
            score = score * 10  # Convert to 0-100 scale
        
        cur.execute("""
            UPDATE resumes SET
                status = 'completed',
                score = %s,
                match_summary = %s,
                skills_matched = %s,
                skills_missing = %s,
                red_flags = %s,
                processed_at = NOW()
            WHERE id = %s
        """, (
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
        raise


def notify_progress(job_id: str, resume_id: str, status: str, score: float = None):
    """Notify backend about screening progress via HTTP"""
    try:
        requests.post(
            f"{BACKEND_URL}/api/v1/screening/progress",
            json={"job_id": job_id, "resume_id": resume_id, "status": status, "score": score},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Failed to notify progress: {e}")


def process_message(ch, method, properties, body):
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
        
        if not resume_text:
            logger.error("No text extracted from file!")
            update_resume_result(resume_id, {
                "score": 0,
                "summary": "Could not extract text from resume file",
                "skills_matched": [],
                "skills_missing": [],
                "red_flags": ["Text extraction failed"]
            })
            notify_progress(job_id, resume_id, "completed", 0)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Score with LLM
        result = score_resume(resume_text, job_description)
        logger.info(f"LLM result: {result}")

        # Save results to DB
        score = result.get("score", 0)
        if score <= 10:
            score = score * 10
        update_resume_result(resume_id, result)
        
        # Notify: completed with score
        notify_progress(job_id, resume_id, "completed", score)

        logger.info(f"Completed resume: {resume_id} | Score: {result.get('score')}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Failed to process resume: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            if 'message' in locals():
                update_resume_result(message.get("resume_id", "unknown"), {
                    "score": 0,
                    "summary": f"Processing failed: {str(e)[:100]}",
                    "skills_matched": [],
                    "skills_missing": [],
                    "red_flags": ["Processing error"]
                })
        except:
            pass
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker():
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Connecting to RabbitMQ (attempt {retry_count + 1})...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                    connection_attempts=3,
                    retry_delay=2
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="resume_queue", durable=True)
            channel.basic_qos(prefetch_count=1)
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
