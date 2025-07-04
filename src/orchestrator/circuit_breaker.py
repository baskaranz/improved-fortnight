"""
Circuit breaker implementation for fault tolerance.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable, Awaitable, List
from enum import Enum

from .models import CircuitBreakerState, CircuitBreakerConfig, FallbackStrategy
from .registry import EndpointRegistry


logger = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for a single endpoint."""
    
    def __init__(self, endpoint_id: str, config: CircuitBreakerConfig) -> None:
        self.endpoint_id = endpoint_id
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.state_changed_time = datetime.now()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute a function through the circuit breaker."""
        async with self._lock:
            current_state = await self._get_state()
            
            if current_state == CircuitBreakerState.OPEN:
                raise CircuitBreakerError(f"Circuit breaker is open for {self.endpoint_id}")
            
            if current_state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerError(f"Half-open call limit exceeded for {self.endpoint_id}")
                self.half_open_calls += 1
        
        # Execute the function
        try:
            result = await func()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state, handling automatic transitions."""
        if self.state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure.total_seconds() >= self.config.reset_timeout:
                    await self._transition_to_half_open()
        
        return self.state
    
    async def _on_success(self) -> None:
        """Handle successful operation."""
        async with self._lock:
            self.last_success_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                # Transition back to closed after successful half-open calls
                await self._transition_to_closed()
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self) -> None:
        """Handle failed operation."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Go back to open on any failure in half-open state
                await self._transition_to_open()
    
    async def _transition_to_open(self) -> None:
        """Transition to open state."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.state_changed_time = datetime.now()
        self.half_open_calls = 0
        
        logger.warning(f"Circuit breaker opened for {self.endpoint_id} "
                      f"(failures: {self.failure_count})")
        await self._notify_state_change(old_state, self.state)
    
    async def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.state_changed_time = datetime.now()
        self.half_open_calls = 0
        
        logger.info(f"Circuit breaker transitioned to half-open for {self.endpoint_id}")
        await self._notify_state_change(old_state, self.state)
    
    async def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.state_changed_time = datetime.now()
        self.failure_count = 0
        self.half_open_calls = 0
        
        logger.info(f"Circuit breaker closed for {self.endpoint_id}")
        await self._notify_state_change(old_state, self.state)
    
    async def _notify_state_change(
        self, 
        old_state: CircuitBreakerState, 
        new_state: CircuitBreakerState
    ) -> None:
        """Notify about state changes (can be extended for metrics/alerts)."""
        # This can be extended to send notifications, update metrics, etc.
        pass
    
    async def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        async with self._lock:
            old_state = self.state
            await self._transition_to_closed()
            logger.info(f"Circuit breaker manually reset for {self.endpoint_id}")
    
    async def trip(self) -> None:
        """Manually trip the circuit breaker to open state."""
        async with self._lock:
            self.failure_count = self.config.failure_threshold
            self.last_failure_time = datetime.now()
            await self._transition_to_open()
            logger.info(f"Circuit breaker manually tripped for {self.endpoint_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "endpoint_id": self.endpoint_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "state_changed_time": self.state_changed_time.isoformat(),
            "half_open_calls": self.half_open_calls,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "reset_timeout": self.config.reset_timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
                "fallback_strategy": self.config.fallback_strategy.value
            }
        }


class FallbackHandler:
    """Handles fallback responses when circuit breaker is open."""
    
    def __init__(self) -> None:
        self.cached_responses: Dict[str, Dict[str, Any]] = {}
    
    async def handle_fallback(
        self,
        endpoint_id: str,
        strategy: FallbackStrategy,
        fallback_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle fallback response based on strategy."""
        
        if strategy == FallbackStrategy.ERROR_RESPONSE:
            return {
                "error": "service_unavailable",
                "message": f"Service {endpoint_id} is currently unavailable",
                "circuit_breaker_state": "open",
                "timestamp": datetime.now().isoformat()
            }
        
        elif strategy == FallbackStrategy.DEFAULT_RESPONSE:
            if fallback_response:
                return fallback_response
            return {
                "message": "Default response - service temporarily unavailable",
                "endpoint_id": endpoint_id,
                "timestamp": datetime.now().isoformat()
            }
        
        elif strategy == FallbackStrategy.CACHED_RESPONSE:
            cached = self.cached_responses.get(endpoint_id)
            if cached:
                cached["_cached"] = True
                cached["_cache_timestamp"] = datetime.now().isoformat()
                return cached
            else:
                # Fall back to error response if no cache available
                return await self.handle_fallback(endpoint_id, FallbackStrategy.ERROR_RESPONSE)
        
        elif strategy == FallbackStrategy.REDIRECT:
            # This would require additional configuration for redirect targets
            return {
                "error": "service_unavailable",
                "message": f"Service {endpoint_id} is unavailable - redirect not configured",
                "circuit_breaker_state": "open",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            return await self.handle_fallback(endpoint_id, FallbackStrategy.ERROR_RESPONSE)
    
    def cache_response(self, endpoint_id: str, response: Dict[str, Any]) -> None:
        """Cache a successful response for fallback purposes."""
        # Only cache successful responses and limit size
        if isinstance(response, dict) and len(str(response)) < 10000:  # 10KB limit
            self.cached_responses[endpoint_id] = {
                **response,
                "_cached_at": datetime.now().isoformat()
            }
            
            # Limit cache size
            if len(self.cached_responses) > 100:
                # Remove oldest entry
                oldest_key = min(
                    self.cached_responses.keys(),
                    key=lambda k: self.cached_responses[k].get("_cached_at", "")
                )
                del self.cached_responses[oldest_key]


class CircuitBreakerManager:
    """Manages circuit breakers for all endpoints."""
    
    def __init__(self, registry: EndpointRegistry, default_config: CircuitBreakerConfig) -> None:
        self.registry = registry
        self.default_config = default_config
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_handler = FallbackHandler()
    
    def get_circuit_breaker(self, endpoint_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for an endpoint."""
        if endpoint_id not in self.circuit_breakers:
            self.circuit_breakers[endpoint_id] = CircuitBreaker(
                endpoint_id, self.default_config
            )
        return self.circuit_breakers[endpoint_id]
    
    async def execute_with_circuit_breaker(
        self,
        endpoint_id: str,
        func: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Execute a function with circuit breaker protection."""
        circuit_breaker = self.get_circuit_breaker(endpoint_id)
        
        try:
            result = await circuit_breaker.call(func)
            
            # Cache successful responses for fallback
            if isinstance(result, dict):
                self.fallback_handler.cache_response(endpoint_id, result)
            
            # Update registry with circuit breaker state
            self.registry.update_circuit_breaker_state(endpoint_id, circuit_breaker.state)
            
            return result
            
        except CircuitBreakerError:
            # Handle fallback
            fallback_response = await self.fallback_handler.handle_fallback(
                endpoint_id,
                self.default_config.fallback_strategy,
                self.default_config.fallback_response
            )
            
            # Update registry with circuit breaker state
            self.registry.update_circuit_breaker_state(endpoint_id, circuit_breaker.state)
            
            return fallback_response
    
    async def reset_circuit_breaker(self, endpoint_id: str) -> bool:
        """Manually reset a circuit breaker."""
        if endpoint_id in self.circuit_breakers:
            await self.circuit_breakers[endpoint_id].reset()
            self.registry.update_circuit_breaker_state(
                endpoint_id, 
                self.circuit_breakers[endpoint_id].state
            )
            return True
        return False
    
    async def trip_circuit_breaker(self, endpoint_id: str) -> bool:
        """Manually trip a circuit breaker."""
        circuit_breaker = self.get_circuit_breaker(endpoint_id)
        await circuit_breaker.trip()
        self.registry.update_circuit_breaker_state(endpoint_id, circuit_breaker.state)
        return True
    
    def get_circuit_breaker_stats(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get circuit breaker statistics for an endpoint."""
        if endpoint_id in self.circuit_breakers:
            return self.circuit_breakers[endpoint_id].get_stats()
        return None
    
    def get_all_circuit_breaker_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return [cb.get_stats() for cb in self.circuit_breakers.values()]
    
    def cleanup_unused_circuit_breakers(self) -> None:
        """Remove circuit breakers for endpoints that no longer exist."""
        active_endpoint_ids = {ep.endpoint_id for ep in self.registry.list_endpoints()}
        
        unused_ids = []
        for endpoint_id in self.circuit_breakers:
            if endpoint_id not in active_endpoint_ids:
                unused_ids.append(endpoint_id)
        
        for endpoint_id in unused_ids:
            del self.circuit_breakers[endpoint_id]
            logger.debug(f"Removed unused circuit breaker for {endpoint_id}")
        
        if unused_ids:
            logger.info(f"Cleaned up {len(unused_ids)} unused circuit breakers")