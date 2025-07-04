"""
Endpoint registry for managing dynamic endpoint registration and unregistration.
"""

import asyncio
import logging
from datetime import datetime
from threading import RLock
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from .models import (
    EndpointConfig,
    RegisteredEndpoint,
    EndpointStatus,
    CircuitBreakerState,
    OrchestratorConfig
)


logger = logging.getLogger(__name__)


class EndpointRegistry:
    """Manages endpoint registration and lifecycle."""
    
    def __init__(self) -> None:
        self._endpoints: Dict[str, RegisteredEndpoint] = {}
        self._lock = RLock()
        self._url_to_id_map: Dict[str, str] = {}
    
    def register_endpoint(self, config: EndpointConfig) -> RegisteredEndpoint:
        """Register a new endpoint."""
        with self._lock:
            endpoint = RegisteredEndpoint(config=config)
            endpoint_id = endpoint.endpoint_id
            endpoint_url = str(config.url)
            
            # Check for conflicts
            if endpoint_id in self._endpoints:
                existing = self._endpoints[endpoint_id]
                if str(existing.config.url) != endpoint_url:
                    raise ValueError(f"Endpoint ID '{endpoint_id}' already exists with different URL")
                
                # Update existing endpoint
                existing.config = config
                existing.registration_time = datetime.now()
                existing.status = EndpointStatus.DISABLED if config.disabled else EndpointStatus.ACTIVE
                logger.info(f"Updated endpoint: {endpoint_id}")
                return existing
            
            # Check for URL conflicts
            if endpoint_url in self._url_to_id_map:
                existing_id = self._url_to_id_map[endpoint_url]
                if existing_id != endpoint_id:
                    raise ValueError(f"URL '{endpoint_url}' already registered with different ID '{existing_id}'")
            
            # Set initial status
            endpoint.status = EndpointStatus.DISABLED if config.disabled else EndpointStatus.ACTIVE
            
            # Register the endpoint
            self._endpoints[endpoint_id] = endpoint
            self._url_to_id_map[endpoint_url] = endpoint_id
            
            logger.info(f"Registered endpoint: {endpoint_id} -> {endpoint_url}")
            return endpoint
    
    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister an endpoint by ID."""
        with self._lock:
            if endpoint_id not in self._endpoints:
                logger.warning(f"Attempted to unregister non-existent endpoint: {endpoint_id}")
                return False
            
            endpoint = self._endpoints[endpoint_id]
            endpoint_url = str(endpoint.config.url)
            
            # Remove from maps
            del self._endpoints[endpoint_id]
            if endpoint_url in self._url_to_id_map:
                del self._url_to_id_map[endpoint_url]
            
            logger.info(f"Unregistered endpoint: {endpoint_id}")
            return True
    
    def get_endpoint(self, endpoint_id: str) -> Optional[RegisteredEndpoint]:
        """Get an endpoint by ID."""
        with self._lock:
            return self._endpoints.get(endpoint_id)
    
    def get_endpoint_by_url(self, url: str) -> Optional[RegisteredEndpoint]:
        """Get an endpoint by URL."""
        with self._lock:
            endpoint_id = self._url_to_id_map.get(url)
            if endpoint_id:
                return self._endpoints.get(endpoint_id)
            return None
    
    def list_endpoints(
        self, 
        status_filter: Optional[EndpointStatus] = None,
        include_disabled: bool = True
    ) -> List[RegisteredEndpoint]:
        """List all registered endpoints with optional filtering."""
        with self._lock:
            endpoints = list(self._endpoints.values())
            
            if not include_disabled:
                endpoints = [ep for ep in endpoints if not ep.config.disabled]
            
            if status_filter:
                endpoints = [ep for ep in endpoints if ep.status == status_filter]
            
            return sorted(endpoints, key=lambda x: x.registration_time)
    
    def get_active_endpoints(self) -> List[RegisteredEndpoint]:
        """Get all active (non-disabled, non-unhealthy) endpoints."""
        return self.list_endpoints(
            status_filter=EndpointStatus.ACTIVE,
            include_disabled=False
        )
    
    def update_endpoint_status(self, endpoint_id: str, status: EndpointStatus) -> bool:
        """Update the status of an endpoint."""
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if not endpoint:
                return False
            
            old_status = endpoint.status
            endpoint.status = status
            
            if old_status != status:
                logger.info(f"Endpoint {endpoint_id} status changed: {old_status} -> {status}")
            
            return True
    
    def update_circuit_breaker_state(
        self, 
        endpoint_id: str, 
        state: CircuitBreakerState
    ) -> bool:
        """Update the circuit breaker state of an endpoint."""
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if not endpoint:
                return False
            
            old_state = endpoint.circuit_breaker_state
            endpoint.circuit_breaker_state = state
            
            if old_state != state:
                logger.info(f"Endpoint {endpoint_id} circuit breaker: {old_state} -> {state}")
            
            return True
    
    def record_failure(self, endpoint_id: str) -> bool:
        """Record a failure for an endpoint."""
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if not endpoint:
                return False
            
            endpoint.consecutive_failures += 1
            endpoint.last_failure_time = datetime.now()
            
            logger.debug(f"Recorded failure for {endpoint_id}: {endpoint.consecutive_failures} consecutive")
            return True
    
    def record_success(self, endpoint_id: str) -> bool:
        """Record a success for an endpoint."""
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if not endpoint:
                return False
            
            endpoint.consecutive_failures = 0
            endpoint.last_failure_time = None
            
            logger.debug(f"Recorded success for {endpoint_id}")
            return True
    
    def update_health_check(self, endpoint_id: str, last_check: datetime) -> bool:
        """Update the last health check time for an endpoint."""
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if not endpoint:
                return False
            
            endpoint.last_health_check = last_check
            return True
    
    def get_endpoints_by_status(self, status: EndpointStatus) -> List[RegisteredEndpoint]:
        """Get all endpoints with a specific status."""
        return self.list_endpoints(status_filter=status)
    
    def get_unhealthy_endpoints(self) -> List[RegisteredEndpoint]:
        """Get all unhealthy endpoints."""
        return self.get_endpoints_by_status(EndpointStatus.UNHEALTHY)
    
    def get_endpoint_count(self) -> int:
        """Get total number of registered endpoints."""
        with self._lock:
            return len(self._endpoints)
    
    def get_active_endpoint_count(self) -> int:
        """Get number of active endpoints."""
        return len(self.get_active_endpoints())
    
    def clear_all(self) -> None:
        """Remove all registered endpoints."""
        with self._lock:
            self._endpoints.clear()
            self._url_to_id_map.clear()
            logger.info("Cleared all registered endpoints")
    
    def bulk_register(self, configs: List[EndpointConfig]) -> List[RegisteredEndpoint]:
        """Register multiple endpoints at once."""
        registered = []
        errors = []
        
        for config in configs:
            try:
                endpoint = self.register_endpoint(config)
                registered.append(endpoint)
            except Exception as e:
                error_msg = f"Failed to register endpoint {config.url}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Bulk registration completed with {len(errors)} errors")
        
        return registered
    
    def sync_with_config(self, config: OrchestratorConfig) -> Dict[str, List[str]]:
        """Synchronize registry with configuration."""
        with self._lock:
            result = {
                "added": [],
                "updated": [],
                "removed": [],
                "errors": []
            }
            
            # Get current endpoint IDs
            current_ids = set(self._endpoints.keys())
            config_ids = set()
            
            # Process configuration endpoints
            for endpoint_config in config.endpoints:
                try:
                    endpoint = RegisteredEndpoint(config=endpoint_config)
                    endpoint_id = endpoint.endpoint_id
                    config_ids.add(endpoint_id)
                    
                    if endpoint_id in current_ids:
                        # Update existing
                        existing = self._endpoints[endpoint_id]
                        if existing.config != endpoint_config:
                            existing.config = endpoint_config
                            existing.status = EndpointStatus.DISABLED if endpoint_config.disabled else EndpointStatus.ACTIVE
                            result["updated"].append(endpoint_id)
                    else:
                        # Add new
                        self.register_endpoint(endpoint_config)
                        result["added"].append(endpoint_id)
                
                except Exception as e:
                    error_msg = f"Failed to sync endpoint {endpoint_config.url}: {e}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Remove endpoints not in config
            removed_ids = current_ids - config_ids
            for endpoint_id in removed_ids:
                if self.unregister_endpoint(endpoint_id):
                    result["removed"].append(endpoint_id)
            
            logger.info(f"Registry sync completed: {len(result['added'])} added, "
                       f"{len(result['updated'])} updated, {len(result['removed'])} removed")
            
            return result
    
    def get_registry_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        with self._lock:
            stats = {
                "total": len(self._endpoints),
                "active": 0,
                "inactive": 0,
                "disabled": 0,
                "unhealthy": 0
            }
            
            for endpoint in self._endpoints.values():
                if endpoint.config.disabled:
                    stats["disabled"] += 1
                elif endpoint.status == EndpointStatus.ACTIVE:
                    stats["active"] += 1
                elif endpoint.status == EndpointStatus.INACTIVE:
                    stats["inactive"] += 1
                elif endpoint.status == EndpointStatus.UNHEALTHY:
                    stats["unhealthy"] += 1
            
            return stats