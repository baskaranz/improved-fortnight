"""
Tests for registry API endpoints.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.orchestrator.registry_api import router
from src.orchestrator.registry import EndpointRegistry
from src.orchestrator.models import (
    EndpointConfig, RegisteredEndpoint, EndpointStatus, 
    CircuitBreakerState, HTTPMethod, AuthType
)


@pytest.fixture
def mock_registry():
    """Mock registry for testing."""
    registry = MagicMock(spec=EndpointRegistry)
    
    # Sample endpoint data
    sample_config = EndpointConfig(
        url="https://api.example.com",
        name="test_api",
        version="v1",
        methods=[HTTPMethod.GET, HTTPMethod.POST],
        auth_type=AuthType.BEARER,
        disabled=False,
        timeout=30
    )
    
    sample_endpoint = RegisteredEndpoint(
        config=sample_config,
        registration_time=datetime(2024, 1, 1, 12, 0, 0).timestamp(),
        status=EndpointStatus.ACTIVE,
        circuit_breaker_state=CircuitBreakerState.CLOSED,
        consecutive_failures=0,
        last_failure_time=None
    )
    
    sample_config_2 = EndpointConfig(
        url="https://api2.example.com",
        name="test_api_2",
        version="v2",
        methods=[HTTPMethod.GET],
        auth_type=AuthType.NONE,
        disabled=True,
        timeout=15
    )
    
    sample_endpoint_2 = RegisteredEndpoint(
        config=sample_config_2,
        registration_time=datetime(2024, 1, 1, 13, 0, 0).timestamp(),
        status=EndpointStatus.DISABLED,
        circuit_breaker_state=CircuitBreakerState.CLOSED,
        consecutive_failures=2,
        last_failure_time=datetime(2024, 1, 1, 14, 0, 0).timestamp()
    )
    
    # Configure mock responses
    registry.list_endpoints.return_value = [sample_endpoint, sample_endpoint_2]
    registry.get_endpoint.return_value = sample_endpoint
    registry.register_endpoint.return_value = sample_endpoint
    registry.unregister_endpoint.return_value = True
    registry.update_endpoint_status.return_value = True
    registry.get_registry_stats.return_value = {
        "total": 2,
        "active": 1,
        "inactive": 0,
        "disabled": 1,
        "unhealthy": 0
    }
    registry.sync_with_config.return_value = {
        "added": ["new_endpoint"],
        "updated": ["test_api"],
        "removed": [],
        "errors": []
    }
    
    return registry


@pytest.fixture
def test_app(mock_registry):
    """Create a test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    
    # Override dependency
    async def override_get_registry():
        return mock_registry
    
    from src.orchestrator.registry_api import get_registry
    app.dependency_overrides[get_registry] = override_get_registry
    
    return app


class TestListEndpoints:
    """Test the list endpoints functionality."""
    
    def test_list_endpoints_success(self, test_app):
        """Test successful endpoint listing."""
        client = TestClient(test_app)
        response = client.get("/registry/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert "total_count" in data
        assert "active_count" in data
        assert "unhealthy_count" in data
        assert "disabled_count" in data
        
        assert len(data["endpoints"]) == 2
        assert data["total_count"] == 2
        assert data["active_count"] == 1
        assert data["disabled_count"] == 1
        
        # Check endpoint structure
        endpoint = data["endpoints"][0]
        assert "endpoint_id" in endpoint
        assert "url" in endpoint
        assert "name" in endpoint
        assert "version" in endpoint
        assert "methods" in endpoint
        assert "auth_type" in endpoint
        assert "disabled" in endpoint
        assert "status" in endpoint
        assert "circuit_breaker_state" in endpoint
    
    def test_list_endpoints_with_status_filter(self, test_app, mock_registry):
        """Test endpoint listing with status filter."""
        # Configure mock to return only active endpoints
        active_endpoint = mock_registry.list_endpoints.return_value[0]
        mock_registry.list_endpoints.return_value = [active_endpoint]
        
        client = TestClient(test_app)
        response = client.get("/registry/endpoints?status=active")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 1
        assert data["endpoints"][0]["status"] == "active"
        
        # Verify the mock was called with correct parameters
        mock_registry.list_endpoints.assert_called_with(
            status_filter=EndpointStatus.ACTIVE,
            include_disabled=True
        )
    
    def test_list_endpoints_exclude_disabled(self, test_app, mock_registry):
        """Test endpoint listing excluding disabled endpoints."""
        # Configure mock to return only non-disabled endpoints
        active_endpoint = mock_registry.list_endpoints.return_value[0]
        mock_registry.list_endpoints.return_value = [active_endpoint]
        
        client = TestClient(test_app)
        response = client.get("/registry/endpoints?include_disabled=false")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the mock was called with correct parameters
        mock_registry.list_endpoints.assert_called_with(
            status_filter=None,
            include_disabled=False
        )
    
    def test_list_endpoints_with_pagination(self, test_app):
        """Test endpoint listing with pagination."""
        client = TestClient(test_app)
        response = client.get("/registry/endpoints?limit=1&offset=1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return total count but limited results
        assert data["total_count"] == 2
    
    def test_list_endpoints_registry_error(self, test_app, mock_registry):
        """Test endpoint listing with registry error."""
        mock_registry.list_endpoints.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        response = client.get("/registry/endpoints")
        
        assert response.status_code == 500
        assert "Failed to list endpoints" in response.json()["detail"]


class TestGetEndpointDetails:
    """Test the get endpoint details functionality."""
    
    def test_get_endpoint_details_success(self, test_app):
        """Test successful endpoint details retrieval."""
        client = TestClient(test_app)
        response = client.get("/registry/endpoints/test_api")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoint_id"] == "test_api"
        assert data["url"] == "https://api.example.com/"  # HttpUrl adds trailing slash
        assert data["name"] == "test_api"
        assert data["version"] == "v1"
        assert data["methods"] == ["GET", "POST"]
        assert data["auth_type"] == "bearer"
        assert data["disabled"] == False
        assert data["status"] == "active"
        assert data["circuit_breaker_state"] == "closed"
        assert data["timeout"] == 30
    
    def test_get_endpoint_details_not_found(self, test_app, mock_registry):
        """Test endpoint details retrieval for non-existent endpoint."""
        mock_registry.get_endpoint.return_value = None
        
        client = TestClient(test_app)
        response = client.get("/registry/endpoints/nonexistent")
        
        assert response.status_code == 404
        assert "Endpoint not found" in response.json()["detail"]
    
    def test_get_endpoint_details_registry_error(self, test_app, mock_registry):
        """Test endpoint details retrieval with registry error."""
        mock_registry.get_endpoint.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        response = client.get("/registry/endpoints/test_api")
        
        assert response.status_code == 500
        assert "Failed to get endpoint details" in response.json()["detail"]


class TestRegisterEndpoint:
    """Test the register endpoint functionality."""
    
    def test_register_endpoint_success(self, test_app):
        """Test successful endpoint registration."""
        client = TestClient(test_app)
        
        endpoint_data = {
            "config": {
                "url": "https://new-api.example.com",
                "name": "new_api",
                "version": "v1",
                "methods": ["GET"],
                "auth_type": "none",
                "disabled": False,
                "timeout": 30
            }
        }
        
        response = client.post("/registry/endpoints", json=endpoint_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["endpoint_id"] == "test_api"
        assert data["endpoint_url"] == "https://api.example.com/"  # HttpUrl adds trailing slash
        assert "successfully" in data["message"]
    
    def test_register_endpoint_validation_error(self, test_app, mock_registry):
        """Test endpoint registration with validation error."""
        mock_registry.register_endpoint.side_effect = ValueError("Invalid configuration")
        
        client = TestClient(test_app)
        
        endpoint_data = {
            "config": {
                "url": "invalid-url",
                "name": "test",
                "methods": ["INVALID"]
            }
        }
        
        response = client.post("/registry/endpoints", json=endpoint_data)
        
        # This will be a 422 validation error from pydantic, not a 400 from our custom validation
        assert response.status_code == 422
    
    def test_register_endpoint_registry_validation_error(self, test_app, mock_registry):
        """Test endpoint registration with registry validation error (400)."""
        mock_registry.register_endpoint.side_effect = ValueError("Invalid configuration")
        
        client = TestClient(test_app)
        
        endpoint_data = {
            "config": {
                "url": "https://api.example.com",
                "name": "test",
                "methods": ["GET"]
            }
        }
        
        response = client.post("/registry/endpoints", json=endpoint_data)
        
        assert response.status_code == 400
        assert "Invalid configuration" in response.json()["detail"]
    
    def test_register_endpoint_registry_error(self, test_app, mock_registry):
        """Test endpoint registration with registry error."""
        mock_registry.register_endpoint.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        
        endpoint_data = {
            "config": {
                "url": "https://api.example.com",
                "name": "test",
                "methods": ["GET"]
            }
        }
        
        response = client.post("/registry/endpoints", json=endpoint_data)
        
        assert response.status_code == 500
        assert "Failed to register endpoint" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint functionality."""
    
    def test_unregister_endpoint_success(self, test_app):
        """Test successful endpoint unregistration."""
        client = TestClient(test_app)
        response = client.delete("/registry/endpoints/test_api")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["endpoint_id"] == "test_api"
        assert "unregistered successfully" in data["message"]
    
    def test_unregister_endpoint_not_found(self, test_app, mock_registry):
        """Test unregistering non-existent endpoint."""
        mock_registry.unregister_endpoint.return_value = False
        
        client = TestClient(test_app)
        response = client.delete("/registry/endpoints/nonexistent")
        
        assert response.status_code == 404
        assert "Endpoint not found" in response.json()["detail"]
    
    def test_unregister_endpoint_registry_error(self, test_app, mock_registry):
        """Test endpoint unregistration with registry error."""
        mock_registry.unregister_endpoint.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        response = client.delete("/registry/endpoints/test_api")
        
        assert response.status_code == 500
        assert "Failed to unregister endpoint" in response.json()["detail"]


class TestUpdateEndpointStatus:
    """Test the update endpoint status functionality."""
    
    def test_update_endpoint_status_success(self, test_app):
        """Test successful endpoint status update."""
        client = TestClient(test_app)
        response = client.put("/registry/endpoints/test_api/status?status=inactive")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["endpoint_id"] == "test_api"
        assert data["new_status"] == "inactive"
        assert "status updated" in data["message"]
    
    def test_update_endpoint_status_not_found(self, test_app, mock_registry):
        """Test updating status of non-existent endpoint."""
        mock_registry.update_endpoint_status.return_value = False
        
        client = TestClient(test_app)
        response = client.put("/registry/endpoints/nonexistent/status?status=inactive")
        
        assert response.status_code == 404
        assert "Endpoint not found" in response.json()["detail"]
    
    def test_update_endpoint_status_registry_error(self, test_app, mock_registry):
        """Test endpoint status update with registry error."""
        mock_registry.update_endpoint_status.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        response = client.put("/registry/endpoints/test_api/status?status=inactive")
        
        assert response.status_code == 500
        assert "Failed to update endpoint status" in response.json()["detail"]


class TestGetRegistryStats:
    """Test the get registry stats functionality."""
    
    def test_get_registry_stats_success(self, test_app):
        """Test successful registry stats retrieval."""
        client = TestClient(test_app)
        response = client.get("/registry/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "registry_stats" in data
        assert "timestamp" in data
        assert "timestamp_iso" in data
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["timestamp_iso"], str)
        
        stats = data["registry_stats"]
        assert stats["total"] == 2
        assert stats["active"] == 1
        assert stats["disabled"] == 1
        assert stats["unhealthy"] == 0
    
    def test_get_registry_stats_registry_error(self, test_app, mock_registry):
        """Test registry stats retrieval with registry error."""
        mock_registry.get_registry_stats.side_effect = Exception("Registry error")
        
        client = TestClient(test_app)
        response = client.get("/registry/stats")
        
        assert response.status_code == 500
        assert "Failed to get registry stats" in response.json()["detail"]


class TestSyncRegistryWithConfig:
    """Test the sync registry with config functionality."""
    
    def test_sync_registry_success(self, test_app):
        """Test successful registry synchronization."""
        from unittest.mock import patch, MagicMock
        from src.orchestrator.models import OrchestratorConfig
        
        client = TestClient(test_app)
        
        # Mock the config manager at the app level where it's imported
        with patch('src.orchestrator.app.get_config_manager') as mock_get_config:
            mock_config_manager = MagicMock()
            mock_config = MagicMock(spec=OrchestratorConfig)
            mock_config_manager.get_config.return_value = mock_config
            mock_get_config.return_value = mock_config_manager
            
            response = client.post("/registry/sync")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] == True
            assert "synchronized" in data["message"]
            assert "sync_result" in data
            assert "timestamp" in data
            
            sync_result = data["sync_result"]
            assert "added" in sync_result
            assert "updated" in sync_result
            assert "removed" in sync_result
            assert "errors" in sync_result
    
    def test_sync_registry_no_config(self, test_app):
        """Test registry sync when no configuration is loaded."""
        from unittest.mock import patch, MagicMock
        
        client = TestClient(test_app)
        
        with patch('src.orchestrator.app.get_config_manager') as mock_get_config:
            mock_config_manager = MagicMock()
            mock_config_manager.get_config.return_value = None
            mock_get_config.return_value = mock_config_manager
            
            response = client.post("/registry/sync")
            
            assert response.status_code == 404
            assert "Configuration not loaded" in response.json()["detail"]
    
    def test_sync_registry_error(self, test_app, mock_registry):
        """Test registry sync with error."""
        mock_registry.sync_with_config.side_effect = Exception("Sync error")
        
        client = TestClient(test_app)
        response = client.post("/registry/sync")
        
        assert response.status_code == 500
        assert "Failed to sync registry" in response.json()["detail"]


class TestRegistryAPIEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_invalid_pagination_parameters(self, test_app):
        """Test with invalid pagination parameters."""
        client = TestClient(test_app)
        
        # Test negative offset
        response = client.get("/registry/endpoints?offset=-1")
        assert response.status_code == 422  # Validation error
        
        # Test limit too large
        response = client.get("/registry/endpoints?limit=2000")
        assert response.status_code == 422  # Validation error
        
        # Test limit too small
        response = client.get("/registry/endpoints?limit=0")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_status_parameter(self, test_app):
        """Test with invalid status parameter."""
        client = TestClient(test_app)
        response = client.get("/registry/endpoints?status=invalid_status")
        
        assert response.status_code == 422  # Validation error
    
    def test_endpoint_response_model_conversion(self, test_app):
        """Test that endpoint response models are properly converted."""
        client = TestClient(test_app)
        response = client.get("/registry/endpoints/test_api")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present and have correct types
        assert isinstance(data["endpoint_id"], str)
        assert isinstance(data["url"], str)
        assert isinstance(data["methods"], list)
        assert isinstance(data["disabled"], bool)
        assert isinstance(data["timeout"], int)
        assert isinstance(data["consecutive_failures"], int)
        
        # Verify datetime fields are properly serialized
        assert "registration_time" in data
        # last_health_check and last_failure_time can be None
    
    def test_large_endpoint_list_pagination(self, test_app, mock_registry):
        """Test pagination with large endpoint lists."""
        # Create a large list of mock endpoints
        large_endpoint_list = []
        for i in range(150):
            config = EndpointConfig(
                url=f"https://api{i}.example.com",
                name=f"api_{i}",
                methods=[HTTPMethod.GET]
            )
            endpoint = RegisteredEndpoint(config=config)
            large_endpoint_list.append(endpoint)
        
        mock_registry.list_endpoints.return_value = large_endpoint_list
        
        client = TestClient(test_app)
        
        # Test first page
        response = client.get("/registry/endpoints?limit=50&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 50
        assert data["total_count"] == 150
        
        # Test middle page
        response = client.get("/registry/endpoints?limit=50&offset=50")
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 50
        
        # Test last page
        response = client.get("/registry/endpoints?limit=50&offset=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 50
    
    def test_empty_registry(self, test_app, mock_registry):
        """Test API behavior with empty registry."""
        mock_registry.list_endpoints.return_value = []
        mock_registry.get_registry_stats.return_value = {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "disabled": 0,
            "unhealthy": 0
        }
        
        client = TestClient(test_app)
        
        # Test list endpoints
        response = client.get("/registry/endpoints")
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 0
        assert data["total_count"] == 0
        
        # Test stats
        response = client.get("/registry/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["registry_stats"]["total"] == 0 