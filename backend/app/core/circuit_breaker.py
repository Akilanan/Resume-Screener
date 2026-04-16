"""
Circuit Breaker Pattern Implementation
Prevents cascade failures when external services (LLM) are down
"""
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import asyncio


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        @breaker
        async def call_llm_api(prompt):
            return await openai_client.complete(prompt)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. Retry after {self.timeout}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
        else:
            self.failures = max(0, self.failures - 1)
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_state(self) -> dict:
        return {
            "state": self.state.value,
            "failures": self.failures,
            "successes": getattr(self, 'successes', 0),
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# Global circuit breakers for different services
llm_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)  # 5 min cooldown
database_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=30)


class CircuitBreakerRegistry:
    """Registry to manage multiple circuit breakers"""
    
    def __init__(self):
        self.breakers = {}
    
    def register(self, name: str, breaker: CircuitBreaker):
        self.breakers[name] = breaker
    
    def get_status(self) -> dict:
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}


registry = CircuitBreakerRegistry()
registry.register("llm_api", llm_circuit_breaker)
registry.register("database", database_circuit_breaker)
