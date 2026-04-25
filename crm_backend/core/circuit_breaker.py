"""Circuit breaker pattern for external API calls.

Uses Redis as shared state storage so all workers see the same circuit state.

States:
    CLOSED   — normal operation, requests pass through.
    OPEN     — failure threshold reached, requests fail fast.
    HALF_OPEN — after cooldown, one probe request allowed.

Usage:
    breaker = CircuitBreaker("email_api", failure_threshold=5, recovery_timeout=60)
    with breaker:
        send_email(...)
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)

REDIS_ALIAS = getattr(settings, "CIRCUIT_BREAKER_CACHE_ALIAS", "default")

# Cache key prefixes
_STATE_PREFIX = "circuit_breaker:state"
_FAILURES_PREFIX = "circuit_breaker:failures"
_LAST_FAILURE_PREFIX = "circuit_breaker:last_failure"


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is OPEN."""

    pass


@dataclass(frozen=True)
class CircuitBreaker:
    """Circuit breaker for external service calls.

    Attributes:
        name: Unique identifier for the external service.
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before trying again (HALF_OPEN).
        success_threshold: Consecutive successes in HALF_OPEN to close.
        timeout: Seconds after which a call is considered a failure.
    """

    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: int = 30

    def _cache(self) -> Any:
        return caches[REDIS_ALIAS]

    def _state_key(self) -> str:
        return f"{_STATE_PREFIX}:{self.name}"

    def _failures_key(self) -> str:
        return f"{_FAILURES_PREFIX}:{self.name}"

    def _last_failure_key(self) -> str:
        return f"{_LAST_FAILURE_PREFIX}:{self.name}"

    def state(self) -> str:
        """Return current circuit state: ``closed``, ``open``, or ``half_open``."""
        cache = self._cache()
        raw = cache.get(self._state_key(), "closed")
        return str(raw)

    def is_open(self) -> bool:
        """Check if circuit is currently OPEN."""
        if self.state() == "open":
            cache = self._cache()
            last_failure = cache.get(self._last_failure_key())
            if last_failure is None:
                return True
            import time

            elapsed = time.time() - float(last_failure)
            if elapsed >= self.recovery_timeout:
                # Transition to half-open
                cache.set(self._state_key(), "half_open")
                cache.set(self._failures_key(), 0)
                logger.info("Circuit breaker %s moved to HALF_OPEN", self.name)
                return False
            return True
        return False

    def record_success(self) -> None:
        """Record a successful call."""
        cache = self._cache()
        # Ensure we are in the correct state (handles transition from open -> half_open)
        _ = self.is_open()
        current_state = self.state()
        if current_state == "half_open":
            successes = cache.get(self._failures_key(), 0) + 1  # re-use key for probe count
            if successes >= self.success_threshold:
                cache.set(self._state_key(), "closed")
                cache.set(self._failures_key(), 0)
                logger.info("Circuit breaker %s CLOSED after recovery", self.name)
            else:
                cache.set(self._failures_key(), successes)
        else:
            cache.set(self._failures_key(), 0)

    def record_failure(self) -> None:
        """Record a failed call."""
        import time

        cache = self._cache()
        failures = cache.get(self._failures_key(), 0) + 1
        cache.set(self._failures_key(), failures)
        cache.set(self._last_failure_key(), time.time())

        if failures >= self.failure_threshold:
            cache.set(self._state_key(), "open")
            logger.warning(
                "Circuit breaker %s OPENED after %d consecutive failures",
                self.name,
                failures,
            )

    @contextmanager
    def circuit(self) -> Generator[None, None, None]:
        """Context manager that wraps an external call with circuit breaker logic.

        Raises:
            CircuitBreakerOpenError: If the circuit is OPEN.
            Exception: Re-raises any exception from the wrapped call.
        """
        if self.is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable.")

        try:
            yield
            self.record_success()
        except Exception as exc:
            self.record_failure()
            raise exc

    def __enter__(self) -> CircuitBreaker:
        if self.is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable.")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
