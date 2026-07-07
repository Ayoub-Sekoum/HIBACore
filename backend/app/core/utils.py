import asyncio
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

from app.core.exceptions import AppException
from app.core.error_codes import ErrorCode

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')

# --- Retry Pattern ---

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    is_async: bool = True
):
    """Retry decorator with exponential backoff for sync or async functions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                last_exception: Exception | None = None
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            sleep_time = backoff_factor ** attempt
                            logger.warning("retry_attempt", func=func.__name__, attempt=attempt+1, sleep=sleep_time, error=str(e))
                            await asyncio.sleep(sleep_time)
                            continue
                        raise
                if last_exception:
                    raise last_exception
                raise AppException(ErrorCode.SYS_503, detail="Retry failed without specific exception")
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                last_exception: Exception | None = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            sleep_time = backoff_factor ** attempt
                            logger.warning("retry_attempt_sync", func=func.__name__, attempt=attempt+1, sleep=sleep_time, error=str(e))
                            time.sleep(sleep_time)
                            continue
                        raise
                if last_exception:
                    raise last_exception
                raise AppException(ErrorCode.SYS_503, detail="Retry failed without specific exception")
            return sync_wrapper
    return decorator

# ---Circuit Breaker Pattern ---

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: datetime | None = None

    async def call_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (datetime.now() - self.last_failure_time > self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("circuit_breaker_half_open", name=self.name)
            else:
                logger.error("circuit_breaker_open_rejected", name=self.name)
                raise AppException(ErrorCode.SYS_503, detail=f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("circuit_breaker_closed", name=self.name)

    def _on_failure(self, error: Exception):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        logger.warning("circuit_breaker_failure", name=self.name, failure_count=self.failure_count, error=str(error))

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_breaker_opened", name=self.name)

# --- Graceful Degradation / Fallback ---

async def with_fallback_async(
    primary: Callable[..., Any],
    fallback: Callable[..., Any],
    *args,
    **kwargs
) -> Any:
    """Try primary async function, fall back to fallback on error."""
    try:
        if asyncio.iscoroutinefunction(primary):
             return await primary(*args, **kwargs)
        return primary(*args, **kwargs)
    except Exception as e:
        logger.warning("graceful_degradation_fallback", primary=str(primary), error=str(e))
        if asyncio.iscoroutinefunction(fallback):
            return await fallback(*args, **kwargs)
        return fallback(*args, **kwargs)
