import pika
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def publish_resume_job(message: dict):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.queue_declare(queue="resume_queue", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="resume_queue",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
        connection.close()
        logger.info(f"Published resume job: {message['resume_id']}")
    except Exception as e:
        logger.error(f"Failed to publish to queue: {e}")
        raise
