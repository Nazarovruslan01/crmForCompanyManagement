"""Tests for circuit breaker."""

import pytest

from core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

pytestmark = pytest.mark.django_db


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_is_closed(self):
        """Fresh circuit breaker is CLOSED."""
        breaker = CircuitBreaker("test_svc_1", failure_threshold=3, recovery_timeout=1)
        assert breaker.state() == "closed"
        assert breaker.is_open() is False

    def test_record_failure_increments_count(self):
        """Recording failures increments the failure counter."""
        breaker = CircuitBreaker("test_svc_2", failure_threshold=3, recovery_timeout=1)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state() == "closed"

    def test_opens_after_threshold_reached(self):
        """Circuit opens after N consecutive failures."""
        breaker = CircuitBreaker("test_svc_3", failure_threshold=2, recovery_timeout=1)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open() is True
        assert breaker.state() == "open"

    def test_success_resets_counter(self):
        """Success resets failure count."""
        breaker = CircuitBreaker("test_svc_4", failure_threshold=3, recovery_timeout=1)
        breaker.record_failure()
        breaker.record_success()
        assert breaker.state() == "closed"

    def test_open_raises_on_enter(self):
        """Entering an OPEN breaker raises CircuitBreakerOpenError."""
        breaker = CircuitBreaker("test_svc_5", failure_threshold=1, recovery_timeout=60)
        breaker.record_failure()
        with pytest.raises(CircuitBreakerOpenError):
            with breaker:
                pass  # should never reach here

    def test_context_manager_records_success(self):
        """Successful block inside context manager records success."""
        breaker = CircuitBreaker("test_svc_6", failure_threshold=2, recovery_timeout=1)
        with breaker:
            pass
        assert breaker.state() == "closed"

    def test_context_manager_records_failure(self):
        """Exception inside context manager records failure."""
        breaker = CircuitBreaker("test_svc_7", failure_threshold=2, recovery_timeout=1)
        with pytest.raises(ValueError):
            with breaker:
                raise ValueError("boom")
        assert breaker.state() == "closed"  # only 1 failure

    def test_half_open_after_recovery_timeout(self):
        """After recovery timeout, circuit moves to HALF_OPEN."""
        breaker = CircuitBreaker("test_svc_8", failure_threshold=1, recovery_timeout=0)
        breaker.record_failure()
        assert breaker.is_open() is False  # timeout = 0 means immediate half-open
        assert breaker.state() == "half_open"

    def test_half_open_successes_close_circuit(self):
        """Enough successes in HALF_OPEN close the circuit."""
        breaker = CircuitBreaker("test_svc_9", failure_threshold=1, recovery_timeout=0, success_threshold=2)
        breaker.record_failure()
        breaker.record_success()
        breaker.record_success()
        assert breaker.state() == "closed"
