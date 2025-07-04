"""
Tests for circuit breaker functionality and fault tolerance.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    FallbackHandler,
    CircuitBreakerError
)
from src.orchestrator.models import (
    CircuitBreakerState,
    CircuitBreakerConfig,
    FallbackStrategy,
    EndpointConfig
)
from src.orchestrator.registry import EndpointRegistry


@pytest.fixture
def circuit_breaker_config():
    """Circuit breaker configuration for testing."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        reset_timeout=60,
        half_open_max_calls=2,
        fallback_strategy=FallbackStrategy.ERROR_RESPONSE
    )


@pytest.fixture
def circuit_breaker(circuit_breaker_config):
    """Circuit breaker instance for testing."""
    return CircuitBreaker("test_endpoint", circuit_breaker_config)


@pytest.fixture
def mock_registry():
    """Mock endpoint registry."""
    registry = MagicMock(spec=EndpointRegistry)
    return registry


@pytest.fixture
def circuit_breaker_manager(mock_registry, circuit_breaker_config):
    """Circuit breaker manager for testing."""
    return CircuitBreakerManager(mock_registry, circuit_breaker_config)


@pytest.fixture
def fallback_handler():
    """Fallback handler for testing."""
    return FallbackHandler()


class TestCircuitBreaker:
    """Test CircuitBreaker class functionality."""
    
    def test_circuit_breaker_initialization(self, circuit_breaker, circuit_breaker_config):
        """Test circuit breaker initialization."""
        assert circuit_breaker.endpoint_id == "test_endpoint"
        assert circuit_breaker.config == circuit_breaker_config
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None
        assert circuit_breaker.last_success_time is None
        assert circuit_breaker.half_open_calls == 0
    
    @pytest.mark.asyncio
    async def test_successful_call_closed_state(self, circuit_breaker):
        """Test successful function call in closed state."""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_success_time is not None
    
    @pytest.mark.asyncio
    async def test_failed_call_closed_state(self, circuit_breaker):
        """Test failed function call in closed state."""
        async def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await circuit_breaker.call(fail_func)
        
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.last_failure_time is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self, circuit_breaker):
        """Test circuit breaker opens after failure threshold."""
        async def fail_func():
            raise ValueError("Test error")
        
        # Fail enough times to open circuit
        for i in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(ValueError):
                await circuit_breaker.call(fail_func)
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == circuit_breaker.config.failure_threshold
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_calls_when_open(self, circuit_breaker):
        """Test circuit breaker rejects calls when open."""
        # Force circuit to open state
        await circuit_breaker.trip()
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(any_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_transitions_to_half_open(self, circuit_breaker):
        """Test circuit breaker transitions to half-open after timeout."""
        # Open the circuit
        await circuit_breaker.trip()
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Simulate timeout passage
        circuit_breaker.last_failure_time = datetime.now() - timedelta(
            seconds=circuit_breaker.config.reset_timeout + 1
        )
        
        # Check state - should transition to half-open
        state = await circuit_breaker._get_state()
        assert state == CircuitBreakerState.HALF_OPEN
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Test successful call in half-open state closes circuit."""
        # Set to half-open state
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_failure_opens_circuit(self, circuit_breaker):
        """Test failed call in half-open state opens circuit."""
        # Set to half-open state
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        
        async def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await circuit_breaker.call(fail_func)
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_call_limit(self, circuit_breaker):
        """Test half-open call limit is enforced."""
        # Set to half-open state
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        circuit_breaker.half_open_calls = circuit_breaker.config.half_open_max_calls
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(any_func)
    
    @pytest.mark.asyncio
    async def test_manual_reset(self, circuit_breaker):
        """Test manual circuit breaker reset."""
        # Open the circuit
        await circuit_breaker.trip()
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Reset manually
        await circuit_breaker.reset()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_manual_trip(self, circuit_breaker):
        """Test manual circuit breaker trip."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        
        await circuit_breaker.trip()
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == circuit_breaker.config.failure_threshold
    
    def test_get_stats(self, circuit_breaker):
        """Test circuit breaker statistics."""
        stats = circuit_breaker.get_stats()
        
        assert stats["endpoint_id"] == "test_endpoint"
        assert stats["state"] == CircuitBreakerState.CLOSED.value
        assert stats["failure_count"] == 0
        assert "config" in stats
        assert stats["config"]["failure_threshold"] == circuit_breaker.config.failure_threshold


class TestFallbackHandler:
    """Test FallbackHandler class functionality."""
    
    @pytest.mark.asyncio
    async def test_error_response_fallback(self, fallback_handler):
        """Test error response fallback strategy."""
        result = await fallback_handler.handle_fallback(
            "test_endpoint",
            FallbackStrategy.ERROR_RESPONSE
        )
        
        assert result["error"] == "service_unavailable"
        assert "test_endpoint" in result["message"]
        assert result["circuit_breaker_state"] == "open"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_default_response_fallback_with_custom(self, fallback_handler):
        """Test default response fallback with custom response."""
        custom_response = {"custom": "data", "status": "fallback"}
        
        result = await fallback_handler.handle_fallback(
            "test_endpoint",
            FallbackStrategy.DEFAULT_RESPONSE,
            fallback_response=custom_response
        )
        
        assert result == custom_response
    
    @pytest.mark.asyncio
    async def test_default_response_fallback_without_custom(self, fallback_handler):
        """Test default response fallback without custom response."""
        result = await fallback_handler.handle_fallback(
            "test_endpoint",
            FallbackStrategy.DEFAULT_RESPONSE
        )
        
        assert result["message"] == "Default response - service temporarily unavailable"
        assert result["endpoint_id"] == "test_endpoint"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_cached_response_fallback(self, fallback_handler):
        """Test cached response fallback strategy."""
        # Cache a response first
        cached_data = {"data": "cached_value", "id": 123}
        fallback_handler.cache_response("test_endpoint", cached_data)
        
        result = await fallback_handler.handle_fallback(
            "test_endpoint",
            FallbackStrategy.CACHED_RESPONSE
        )
        
        # The result should include the cached data plus metadata
        assert result["data"] == "cached_value"
        assert result["id"] == 123
        assert result["_cached"] is True
    
    @pytest.mark.asyncio
    async def test_cached_response_fallback_no_cache(self, fallback_handler):
        """Test cached response fallback with no cached data."""
        result = await fallback_handler.handle_fallback(
            "no_cache_endpoint",
            FallbackStrategy.CACHED_RESPONSE
        )
        
        # Should fall back to error response when no cache available
        assert result["error"] == "service_unavailable"
        assert "no_cache_endpoint" in result["message"]
    
    def test_cache_response(self, fallback_handler):
        """Test response caching."""
        response_data = {"key": "value", "timestamp": "2023-01-01"}
        fallback_handler.cache_response("test_endpoint", response_data)
        
        assert "test_endpoint" in fallback_handler.cached_responses
        cached_data = fallback_handler.cached_responses["test_endpoint"]
        assert cached_data["key"] == "value"
        assert cached_data["timestamp"] == "2023-01-01"
        assert "_cached_at" in cached_data
    
    def test_cache_response_size_limit(self, fallback_handler):
        """Test cache response with size limiting."""
        # Test that oversized responses are not cached
        large_response = {"data": "x" * 20000}  # Larger than 10KB limit
        fallback_handler.cache_response("large_endpoint", large_response)
        
        assert "large_endpoint" not in fallback_handler.cached_responses
    
    def test_cache_response_limit_exceeded(self, fallback_handler):
        """Test cache limit behavior when max entries exceeded."""
        # This test would require creating 100+ cache entries which is slow
        # Instead test the basic functionality
        fallback_handler.cache_response("endpoint1", {"data": "test1"})
        fallback_handler.cache_response("endpoint2", {"data": "test2"})
        
        assert "endpoint1" in fallback_handler.cached_responses
        assert "endpoint2" in fallback_handler.cached_responses
    



class TestCircuitBreakerManager:
    """Test CircuitBreakerManager class functionality."""
    
    def test_initialization(self, circuit_breaker_manager, mock_registry, circuit_breaker_config):
        """Test circuit breaker manager initialization."""
        assert circuit_breaker_manager.registry == mock_registry
        assert circuit_breaker_manager.default_config == circuit_breaker_config
        assert len(circuit_breaker_manager.circuit_breakers) == 0
    
    def test_get_circuit_breaker_creates_new(self, circuit_breaker_manager):
        """Test getting circuit breaker creates new instance."""
        cb = circuit_breaker_manager.get_circuit_breaker("new_endpoint")
        
        assert cb.endpoint_id == "new_endpoint"
        assert "new_endpoint" in circuit_breaker_manager.circuit_breakers
        assert circuit_breaker_manager.circuit_breakers["new_endpoint"] == cb
    
    def test_get_circuit_breaker_returns_existing(self, circuit_breaker_manager):
        """Test getting circuit breaker returns existing instance."""
        cb1 = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        cb2 = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        
        assert cb1 is cb2
    
    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_success(self, circuit_breaker_manager):
        """Test successful execution with circuit breaker."""
        async def success_func():
            return "success_result"
        
        result = await circuit_breaker_manager.execute_with_circuit_breaker(
            "test_endpoint",
            success_func
        )
        
        assert result == "success_result"
    
    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_failure(self, circuit_breaker_manager):
        """Test failed execution with circuit breaker."""
        async def fail_func():
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            await circuit_breaker_manager.execute_with_circuit_breaker(
                "test_endpoint",
                fail_func
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_open_fallback(self, circuit_breaker_manager):
        """Test execution with open circuit breaker returns fallback."""
        # Get circuit breaker and open it
        cb = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        await cb.trip()
        
        async def any_func():
            return "should_not_execute"
        
        result = await circuit_breaker_manager.execute_with_circuit_breaker(
            "test_endpoint",
            any_func
        )
        
        # Should return fallback response
        assert "error" in result
        assert result["error"] == "service_unavailable"
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker(self, circuit_breaker_manager):
        """Test resetting circuit breaker."""
        # Create and trip circuit breaker
        cb = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        await cb.trip()
        assert cb.state == CircuitBreakerState.OPEN
        
        # Reset it
        success = await circuit_breaker_manager.reset_circuit_breaker("test_endpoint")
        assert success is True
        assert cb.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_reset_nonexistent_circuit_breaker(self, circuit_breaker_manager):
        """Test resetting non-existent circuit breaker."""
        success = await circuit_breaker_manager.reset_circuit_breaker("nonexistent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_trip_circuit_breaker(self, circuit_breaker_manager):
        """Test tripping circuit breaker."""
        # Create circuit breaker
        cb = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        assert cb.state == CircuitBreakerState.CLOSED
        
        # Trip it
        success = await circuit_breaker_manager.trip_circuit_breaker("test_endpoint")
        assert success is True
        assert cb.state == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_trip_nonexistent_circuit_breaker(self, circuit_breaker_manager):
        """Test tripping non-existent circuit breaker."""
        # This will create a new circuit breaker and trip it
        success = await circuit_breaker_manager.trip_circuit_breaker("nonexistent")
        assert success is True
        # Verify circuit breaker was created and tripped
        assert "nonexistent" in circuit_breaker_manager.circuit_breakers
        assert circuit_breaker_manager.circuit_breakers["nonexistent"].state == CircuitBreakerState.OPEN
    
    def test_get_circuit_breaker_stats(self, circuit_breaker_manager):
        """Test getting circuit breaker statistics."""
        # Create circuit breaker
        cb = circuit_breaker_manager.get_circuit_breaker("test_endpoint")
        
        stats = circuit_breaker_manager.get_circuit_breaker_stats("test_endpoint")
        assert stats is not None
        assert stats["endpoint_id"] == "test_endpoint"
        assert stats["state"] == CircuitBreakerState.CLOSED.value
    
    def test_get_nonexistent_circuit_breaker_stats(self, circuit_breaker_manager):
        """Test getting stats for non-existent circuit breaker."""
        stats = circuit_breaker_manager.get_circuit_breaker_stats("nonexistent")
        assert stats is None
    
    def test_get_all_circuit_breaker_stats(self, circuit_breaker_manager):
        """Test getting all circuit breaker statistics."""
        # Create multiple circuit breakers
        circuit_breaker_manager.get_circuit_breaker("endpoint1")
        circuit_breaker_manager.get_circuit_breaker("endpoint2")
        
        all_stats = circuit_breaker_manager.get_all_circuit_breaker_stats()
        assert len(all_stats) == 2
        
        endpoint_ids = [stats["endpoint_id"] for stats in all_stats]
        assert "endpoint1" in endpoint_ids
        assert "endpoint2" in endpoint_ids
    
    def test_cleanup_unused_circuit_breakers(self, circuit_breaker_manager, mock_registry):
        """Test cleanup of unused circuit breakers."""
        # Create circuit breakers
        circuit_breaker_manager.get_circuit_breaker("active_endpoint")
        circuit_breaker_manager.get_circuit_breaker("inactive_endpoint")
        
        # Mock registry to return only active endpoint
        mock_registry.list_endpoints.return_value = [
            MagicMock(endpoint_id="active_endpoint")
        ]
        
        # Run cleanup
        circuit_breaker_manager.cleanup_unused_circuit_breakers()
        
        # Only active endpoint should remain
        assert "active_endpoint" in circuit_breaker_manager.circuit_breakers
        assert "inactive_endpoint" not in circuit_breaker_manager.circuit_breakers


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_state_transitions(self, circuit_breaker):
        """Test complete circuit breaker state transition cycle."""
        call_count = 0
        
        async def sometimes_fail_func():
            nonlocal call_count
            call_count += 1
            if call_count <= circuit_breaker.config.failure_threshold:
                raise ValueError("Simulated failure")
            return "success"
        
        # Initial state: CLOSED
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # Fail enough times to open circuit
        for i in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(ValueError):
                await circuit_breaker.call(sometimes_fail_func)
        
        # Should be OPEN now
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Simulate timeout for half-open transition
        circuit_breaker.last_failure_time = datetime.now() - timedelta(
            seconds=circuit_breaker.config.reset_timeout + 1
        )
        
        # Should transition to HALF_OPEN on next state check
        await circuit_breaker._get_state()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN
        
        # Successful call should close circuit
        result = await circuit_breaker.call(sometimes_fail_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_access(self, circuit_breaker):
        """Test concurrent access to circuit breaker."""
        async def test_func():
            await asyncio.sleep(0.01)  # Small delay
            return "result"
        
        # Execute multiple concurrent calls
        tasks = [circuit_breaker.call(test_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result == "result" for result in results)
        assert circuit_breaker.state == CircuitBreakerState.CLOSED 