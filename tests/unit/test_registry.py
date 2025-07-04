"""
Unit tests for endpoint registry.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.orchestrator.registry import EndpointRegistry
from src.orchestrator.models import (
    EndpointConfig,
    RegisteredEndpoint,
    EndpointStatus,
    CircuitBreakerState,
    OrchestratorConfig,
    HTTPMethod,
    AuthType
)


@pytest.fixture
def registry():
    """Create a fresh endpoint registry."""
    return EndpointRegistry()


@pytest.fixture
def sample_endpoint_config():
    """Create a sample endpoint configuration."""
    return EndpointConfig(
        url="https://api.example.com/v1/users",
        name="test_endpoint",
        version="v1",
        methods=[HTTPMethod.GET, HTTPMethod.POST],
        auth_type=AuthType.NONE,
        timeout=30
    )


@pytest.fixture
def another_endpoint_config():
    """Create another sample endpoint configuration."""
    return EndpointConfig(
        url="https://api.example.com/v1/posts",
        name="test_posts",
        version="v1",
        methods=[HTTPMethod.GET],
        auth_type=AuthType.BEARER,
        timeout=45
    )


class TestEndpointRegistry:
    """Test cases for EndpointRegistry."""
    
    def test_register_endpoint(self, registry, sample_endpoint_config):
        """Test registering a new endpoint."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        assert isinstance(endpoint, RegisteredEndpoint)
        assert endpoint.config == sample_endpoint_config
        assert endpoint.status == EndpointStatus.ACTIVE
        assert endpoint.endpoint_id == "test_endpoint"
        assert registry.get_endpoint_count() == 1
    
    def test_register_disabled_endpoint(self, registry):
        """Test registering a disabled endpoint."""
        config = EndpointConfig(
            url="https://api.example.com/disabled",
            name="disabled_endpoint",
            disabled=True
        )
        
        endpoint = registry.register_endpoint(config)
        assert endpoint.status == EndpointStatus.DISABLED
    
    def test_register_duplicate_endpoint_id(self, registry, sample_endpoint_config):
        """Test registering endpoint with duplicate ID updates existing."""
        # Register first endpoint
        endpoint1 = registry.register_endpoint(sample_endpoint_config)
        
        # Register endpoint with same name but different URL should update
        updated_config = EndpointConfig(
            url="https://api.example.com/v1/users",  # Same URL
            name="test_endpoint",  # Same name
            version="v2",  # Different version
            timeout=60
        )
        
        endpoint2 = registry.register_endpoint(updated_config)
        
        # Should be the same endpoint object, updated
        assert endpoint1 is endpoint2
        assert endpoint2.config.version == "v2"
        assert endpoint2.config.timeout == 60
        assert registry.get_endpoint_count() == 1
    
    def test_register_duplicate_url_different_id_fails(self, registry, sample_endpoint_config):
        """Test registering same URL with different ID fails."""
        # Register first endpoint
        registry.register_endpoint(sample_endpoint_config)
        
        # Try to register same URL with different name
        conflicting_config = EndpointConfig(
            url="https://api.example.com/v1/users",  # Same URL
            name="different_name",  # Different name
        )
        
        with pytest.raises(ValueError, match="URL .* already registered"):
            registry.register_endpoint(conflicting_config)
    
    def test_unregister_endpoint(self, registry, sample_endpoint_config):
        """Test unregistering an endpoint."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        # Unregister endpoint
        success = registry.unregister_endpoint(endpoint_id)
        
        assert success is True
        assert registry.get_endpoint(endpoint_id) is None
        assert registry.get_endpoint_count() == 0
    
    def test_unregister_nonexistent_endpoint(self, registry):
        """Test unregistering a non-existent endpoint."""
        success = registry.unregister_endpoint("nonexistent")
        assert success is False
    
    def test_get_endpoint(self, registry, sample_endpoint_config):
        """Test getting an endpoint by ID."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        retrieved = registry.get_endpoint(endpoint_id)
        assert retrieved is endpoint
        
        # Test non-existent endpoint
        assert registry.get_endpoint("nonexistent") is None
    
    def test_get_endpoint_by_url(self, registry, sample_endpoint_config):
        """Test getting an endpoint by URL."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        url = str(sample_endpoint_config.url)
        
        retrieved = registry.get_endpoint_by_url(url)
        assert retrieved is endpoint
        
        # Test non-existent URL
        assert registry.get_endpoint_by_url("https://nonexistent.com") is None
    
    def test_list_endpoints(self, registry, sample_endpoint_config, another_endpoint_config):
        """Test listing endpoints with filtering."""
        endpoint1 = registry.register_endpoint(sample_endpoint_config)
        endpoint2 = registry.register_endpoint(another_endpoint_config)
        
        # List all endpoints
        all_endpoints = registry.list_endpoints()
        assert len(all_endpoints) == 2
        
        # Test status filtering
        registry.update_endpoint_status(endpoint1.endpoint_id, EndpointStatus.UNHEALTHY)
        unhealthy_endpoints = registry.list_endpoints(status_filter=EndpointStatus.UNHEALTHY)
        assert len(unhealthy_endpoints) == 1
        assert unhealthy_endpoints[0] is endpoint1
    
    def test_list_endpoints_exclude_disabled(self, registry):
        """Test listing endpoints excluding disabled ones."""
        # Register active endpoint
        active_config = EndpointConfig(url="https://api.example.com/active", name="active")
        registry.register_endpoint(active_config)
        
        # Register disabled endpoint
        disabled_config = EndpointConfig(url="https://api.example.com/disabled", name="disabled", disabled=True)
        registry.register_endpoint(disabled_config)
        
        # List without disabled
        active_endpoints = registry.list_endpoints(include_disabled=False)
        assert len(active_endpoints) == 1
        assert active_endpoints[0].endpoint_id == "active"
    
    def test_get_active_endpoints(self, registry, sample_endpoint_config, another_endpoint_config):
        """Test getting only active endpoints."""
        endpoint1 = registry.register_endpoint(sample_endpoint_config)
        endpoint2 = registry.register_endpoint(another_endpoint_config)
        
        # Make one unhealthy
        registry.update_endpoint_status(endpoint1.endpoint_id, EndpointStatus.UNHEALTHY)
        
        active_endpoints = registry.get_active_endpoints()
        assert len(active_endpoints) == 1
        assert active_endpoints[0] is endpoint2
    
    def test_update_endpoint_status(self, registry, sample_endpoint_config):
        """Test updating endpoint status."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        # Update status
        success = registry.update_endpoint_status(endpoint_id, EndpointStatus.UNHEALTHY)
        assert success is True
        assert endpoint.status == EndpointStatus.UNHEALTHY
        
        # Test non-existent endpoint
        success = registry.update_endpoint_status("nonexistent", EndpointStatus.ACTIVE)
        assert success is False
    
    def test_update_circuit_breaker_state(self, registry, sample_endpoint_config):
        """Test updating circuit breaker state."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        # Update circuit breaker state
        success = registry.update_circuit_breaker_state(endpoint_id, CircuitBreakerState.OPEN)
        assert success is True
        assert endpoint.circuit_breaker_state == CircuitBreakerState.OPEN
        
        # Test non-existent endpoint
        success = registry.update_circuit_breaker_state("nonexistent", CircuitBreakerState.CLOSED)
        assert success is False
    
    def test_record_failure(self, registry, sample_endpoint_config):
        """Test recording endpoint failures."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        # Record failures
        registry.record_failure(endpoint_id)
        assert endpoint.consecutive_failures == 1
        assert endpoint.last_failure_time is not None
        
        registry.record_failure(endpoint_id)
        assert endpoint.consecutive_failures == 2
        
        # Test non-existent endpoint
        success = registry.record_failure("nonexistent")
        assert success is False
    
    def test_record_success(self, registry, sample_endpoint_config):
        """Test recording endpoint success."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        # First record some failures
        endpoint.consecutive_failures = 3
        endpoint.last_failure_time = datetime.now()
        
        # Record success
        registry.record_success(endpoint_id)
        assert endpoint.consecutive_failures == 0
        assert endpoint.last_failure_time is None
        
        # Test non-existent endpoint
        success = registry.record_success("nonexistent")
        assert success is False
    
    def test_update_health_check(self, registry, sample_endpoint_config):
        """Test updating health check timestamp."""
        endpoint = registry.register_endpoint(sample_endpoint_config)
        endpoint_id = endpoint.endpoint_id
        
        now = datetime.now()
        success = registry.update_health_check(endpoint_id, now)
        
        assert success is True
        assert endpoint.last_health_check == now
        
        # Test non-existent endpoint
        success = registry.update_health_check("nonexistent", now)
        assert success is False
    
    def test_get_registry_stats(self, registry):
        """Test getting registry statistics."""
        # Start with empty registry
        stats = registry.get_registry_stats()
        assert stats["total"] == 0
        assert stats["active"] == 0
        
        # Add endpoints with different statuses
        active_config = EndpointConfig(url="https://api.example.com/active", name="active")
        disabled_config = EndpointConfig(url="https://api.example.com/disabled", name="disabled", disabled=True)
        
        active_endpoint = registry.register_endpoint(active_config)
        registry.register_endpoint(disabled_config)
        
        # Make one unhealthy
        registry.update_endpoint_status(active_endpoint.endpoint_id, EndpointStatus.UNHEALTHY)
        
        stats = registry.get_registry_stats()
        assert stats["total"] == 2
        assert stats["disabled"] == 1
        assert stats["unhealthy"] == 1
        assert stats["active"] == 0
    
    def test_clear_all(self, registry, sample_endpoint_config, another_endpoint_config):
        """Test clearing all endpoints."""
        registry.register_endpoint(sample_endpoint_config)
        registry.register_endpoint(another_endpoint_config)
        
        assert registry.get_endpoint_count() == 2
        
        registry.clear_all()
        
        assert registry.get_endpoint_count() == 0
        assert len(registry.list_endpoints()) == 0
    
    def test_bulk_register(self, registry):
        """Test bulk registration of endpoints."""
        configs = [
            EndpointConfig(url="https://api1.example.com", name="api1"),
            EndpointConfig(url="https://api2.example.com", name="api2"),
        ]
        
        endpoints = registry.bulk_register(configs)
        
        assert len(endpoints) == 2
        assert registry.get_endpoint_count() == 2
    
    def test_sync_with_config(self, registry):
        """Test synchronizing registry with configuration."""
        # Register initial endpoints
        initial_config = EndpointConfig(url="https://api1.example.com", name="api1")
        registry.register_endpoint(initial_config)
        
        # Create new configuration
        config = OrchestratorConfig(
            endpoints=[
                EndpointConfig(url="https://api1.example.com", name="api1", version="v2"),  # Updated
                EndpointConfig(url="https://api2.example.com", name="api2"),  # New
                # api3 will be removed
            ]
        )
        
        result = registry.sync_with_config(config)
        
        assert len(result["added"]) == 1  # api2
        assert len(result["updated"]) == 1  # api1
        assert len(result["removed"]) == 0  # No removals since api1 was updated
        
        assert registry.get_endpoint_count() == 2
        
        # Check updated endpoint
        api1 = registry.get_endpoint("api1")
        assert api1.config.version == "v2"