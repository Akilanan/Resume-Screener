"""
Retry Handler with Dead Letter Queue
Ensures failed jobs are retried with exponential backoff
"""
import json
import logging
from datetime import datetime
from typing import Callable, Any
import time

logger = logging.getLogger(__name__)


class RetryHandler:
    """
    Handles retry logic with exponential backoff
    
    Usage in worker:
        retry = RetryHandler(max_retries=3)
        
        async def process_resume(data):
            await retry.execute(
                func=analyze_resume,
                data=data,
                on_failure=send_to_dlq
            )
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)
    
    async def execute(
        self,
        func: Callable,
        data: dict,
        on_failure: Callable = None,
        on_success: Callable = None
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            data: Data to pass to function (must include 'retry_count')
            on_failure: Callback when all retries exhausted
            on_success: Callback on successful execution
        """
        retry_count = data.get('retry_count', 0)
        
        for attempt in range(retry_count, self.max_retries + 1):
            try:
                data['retry_count'] = attempt
                result = await func(data)
                
                if on_success:
                    await on_success(data, result)
                
                return result
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt + 1)
                    logger.info(f"Retrying in {delay:.1f}s (attempt {attempt + 2}/{self.max_retries + 1})")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    
                    if on_failure:
                        await on_failure(data, e)
                    
                    raise
        
        return None


class DeadLetterQueueHandler:
    """
    Handles messages that failed all retries
    
    Usage:
        dlq = DeadLetterQueueHandler(rabbitmq_channel)
        
        async def on_failure(data, error):
            await dlq.send_to_dlq(data, error)
    """
    
    def __init__(self, channel, dlq_name: str = "resume_dlq"):
        self.channel = channel
        self.dlq_name = dlq_name
        self._declare_queue()
    
    def _declare_queue(self):
        """Declare the DLQ queue"""
        try:
            self.channel.queue_declare(queue=self.dlq_name, durable=True)
        except Exception as e:
            logger.error(f"Failed to declare DLQ: {e}")
    
    async def send_to_dlq(self, data: dict, error: Exception):
        """Send failed message to DLQ with error details"""
        
        dlq_message = {
            "original_message": data,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            },
            "retry_count": data.get('retry_count', 0),
            "final_failure_time": datetime.utcnow().isoformat()
        }
        
        try:
            # Note: pika (RabbitMQ client) is synchronous
            import pika
            self.channel.basic_publish(
                exchange='',
                routing_key=self.dlq_name,
                body=json.dumps(dlq_message).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Message sent to DLQ: {data.get('resume_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def get_dlq_size(self) -> int:
        """Get number of messages in DLQ"""
        try:
            result = self.channel.queue_declare(queue=self.dlq_name, passive=True)
            return result.method.message_count
        except Exception:
            return 0


# Simple notification function
def notify_admin(resume_id: str, error: str):
    """
    Send notification for manual review
    This could be email, Slack, etc.
    """
    logger.critical(f"ALERT: Resume {resume_id} requires manual review. Error: {error}")
    # TODO: Implement actual notification (email, Slack webhook, etc.)


import asyncio
