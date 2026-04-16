import pika
import json
import logging
import time
from llm_scorer import score_resume
from pdf_extractor import extract_text_from_pdf
import psycopg2
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    import psycopg2
    conn = psycopg2.connect(DB_URL)
    return conn


def update_resume_result(resume_id: str, result: dict):
    conn = get_db_connection()
    cur = conn.cursor()
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
        result["score"],
        result["summary"],
        json.dumps(result["skills_matched"]),
        json.dumps(result["skills_missing"]),
        json.dumps(result["red_flags"]),
        resume_id,
    ))
    conn.commit()
    cur.close()
    conn.close()


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body)
        resume_id = message["resume_id"]
        file_path = message["file_path"]
        job_description = message["job_description"]

        logger.info(f"Processing resume: {resume_id}")

        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)

        # Score with LLM
        result = score_resume(resume_text, job_description)

        # Save results to DB
        update_resume_result(resume_id, result)

        logger.info(f"Completed resume: {resume_id} | Score: {result['score']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Failed to process resume {body}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker():
    # Retry connection to RabbitMQ (it may start slow)
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "rabbitmq"))
            )
            channel = connection.channel()
            channel.queue_declare(queue="resume_queue", durable=True)
            channel.basic_qos(prefetch_count=1)  # One at a time per worker (idempotency)
            channel.basic_consume(queue="resume_queue", on_message_callback=process_message)
            logger.info("Worker started. Waiting for messages...")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Connection failed, retrying in 5s: {e}")
            time.sleep(5)


if __name__ == "__main__":
    start_worker()
