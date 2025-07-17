"""
Tests for configuration API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from src.orchestrator.config_api import router, ReloadResponse, ConfigStatusResponse
from src.orchestrator.config import ConfigManager
from src.orchestrator.models import OrchestratorConfig, EndpointConfig


@pytest.fixture
def mock_config_manager():
    """Mock config manager for testing."""
    config_manager = MagicMock(spec=ConfigManager)
    
    # Mock config
    sample_config = OrchestratorConfig(
        endpoints=[
            EndpointConfig(
                url="https://api.example.com",
                name="test_api",
                version="v1",
                methods=["GET", "POST"]
            )
        ]
    )
    
    config_manager.get_config.return_value = sample_config
    config_manager.get_status.return_value = {
        "loaded": True,
        "version": "1.0.0",
        "config_path": "/config/config.yaml",
        "endpoints_count": 1,
        "watching": True,
        "last_reload_error": None
    }
    
    return config_manager


@pytest.fixture
def test_app(mock_config_manager):
    """Test FastAPI application with config API."""
    app = FastAPI()
    
    # Mock the dependency
    def get_mock_config_manager():
        return mock_config_manager
    
    # Override the dependency
    from src.orchestrator.config_api import get_config_manager
    app.dependency_overrides[get_config_manager] = get_mock_config_manager
    
    # Include the router
    app.include_router(router)
    
    return app


class TestConfigurationAPI:
    """Test configuration API endpoints."""
    
    def test_reload_configuration_success(self, test_app, mock_config_manager):
        """Test successful configuration reload."""
        # Mock successful reload
        reloaded_config = OrchestratorConfig(
            endpoints=[
                EndpointConfig(
                    url="https://api.example.com",
                    name="test_api",
                    version="v1"
                ),
                EndpointConfig(
                    url="https://api2.example.com",
                    name="test_api2",
                    version="v1"
                )
            ]
        )
        mock_config_manager.reload_config = AsyncMock(return_value=reloaded_config)
        
        client = TestClient(test_app)
        response = client.post("/config/reload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Configuration reloaded successfully"
        assert data["endpoints_count"] == 2
        assert data["errors"] == []
        
        # Verify reload was called
        mock_config_manager.reload_config.assert_called_once()
    
    def test_reload_configuration_failure(self, test_app, mock_config_manager):
        """Test configuration reload failure."""
        # Mock reload failure
        mock_config_manager.reload_config = AsyncMock(
            side_effect=Exception("Config file not found")
        )
        
        client = TestClient(test_app)
        response = client.post("/config/reload")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to reload configuration" in data["detail"]
        assert "Config file not found" in data["detail"]
    
    def test_get_configuration_status_success(self, test_app, mock_config_manager):
        """Test getting configuration status successfully."""
        client = TestClient(test_app)
        response = client.get("/config/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["loaded"] is True
        assert data["version"] == "1.0.0"
        assert data["config_path"] == "/config/config.yaml"
        assert data["endpoints_count"] == 1
        assert data["watching"] is True
        assert data["last_reload_error"] is None
        
        # Verify get_status was called
        mock_config_manager.get_status.assert_called_once()
    
    def test_get_configuration_status_with_error(self, test_app, mock_config_manager):
        """Test getting configuration status with last reload error."""
        # Mock status with error
        mock_config_manager.get_status.return_value = {
            "loaded": True,
            "version": "1.0.0",
            "config_path": "/config/config.yaml",
            "endpoints_count": 1,
            "watching": True,
            "last_reload_error": "Previous reload failed"
        }
        
        client = TestClient(test_app)
        response = client.get("/config/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["last_reload_error"] == "Previous reload failed"
    
    def test_get_configuration_status_failure(self, test_app, mock_config_manager):
        """Test configuration status retrieval failure."""
        # Mock get_status failure
        mock_config_manager.get_status.side_effect = Exception("Status unavailable")
        
        client = TestClient(test_app)
        response = client.get("/config/status")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to get configuration status" in data["detail"]
        assert "Status unavailable" in data["detail"]
    
    def test_list_configured_endpoints_success(self, test_app, mock_config_manager):
        """Test listing configured endpoints successfully."""
        # Mock config with multiple endpoints
        config_with_endpoints = OrchestratorConfig(
            endpoints=[
                EndpointConfig(
                    url="https://api.example.com",
                    name="api1",
                    version="v1",
                    methods=["GET", "POST"],
                    disabled=False,
                    health_check_path="/health",
                    timeout=30
                ),
                EndpointConfig(
                    url="https://api2.example.com",
                    name="api2",
                    version="v2",
                    methods=["GET"],
                    disabled=True,
                    timeout=60
                )
            ]
        )
        mock_config_manager.get_config.return_value = config_with_endpoints
        
        client = TestClient(test_app)
        response = client.get("/config/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert len(data["endpoints"]) == 2
        assert data["total_count"] == 2
        assert data["disabled_count"] == 1
        assert data["active_count"] == 1
        
        # Check first endpoint details
        endpoint1 = data["endpoints"][0]
        assert endpoint1["url"] == "https://api.example.com/"
        assert endpoint1["name"] == "api1"
        assert endpoint1["version"] == "v1"
        assert endpoint1["methods"] == ["GET", "POST"]
        assert endpoint1["disabled"] is False
        assert endpoint1["health_check_path"] == "/health"
        assert endpoint1["timeout"] == 30
        
        # Check second endpoint details
        endpoint2 = data["endpoints"][1]
        assert endpoint2["url"] == "https://api2.example.com/"
        assert endpoint2["name"] == "api2"
        assert endpoint2["version"] == "v2"
        assert endpoint2["methods"] == ["GET"]
        assert endpoint2["disabled"] is True
        assert endpoint2["timeout"] == 60
    
    def test_list_configured_endpoints_no_config(self, test_app, mock_config_manager):
        """Test listing endpoints when no configuration is loaded."""
        # Mock no config loaded
        mock_config_manager.get_config.return_value = None
        
        client = TestClient(test_app)
        response = client.get("/config/endpoints")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"] == "Configuration not loaded"
    
    def test_list_configured_endpoints_empty_config(self, test_app, mock_config_manager):
        """Test listing endpoints with empty configuration."""
        # Mock empty config
        empty_config = OrchestratorConfig(endpoints=[])
        mock_config_manager.get_config.return_value = empty_config
        
        client = TestClient(test_app)
        response = client.get("/config/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoints"] == []
        assert data["total_count"] == 0
        assert data["disabled_count"] == 0
        assert data["active_count"] == 0
    
    def test_list_configured_endpoints_failure(self, test_app, mock_config_manager):
        """Test listing endpoints with general failure."""
        # Mock get_config failure
        mock_config_manager.get_config.side_effect = Exception("Config access error")
        
        client = TestClient(test_app)
        response = client.get("/config/endpoints")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to list configured endpoints" in data["detail"]
        assert "Config access error" in data["detail"]


class TestConfigurationModels:
    """Test configuration API response models."""
    
    def test_reload_response_model(self):
        """Test ReloadResponse model."""
        response = ReloadResponse(
            success=True,
            message="Configuration reloaded successfully",
            endpoints_count=5,
            errors=["Warning: deprecated field"]
        )
        
        assert response.success is True
        assert response.message == "Configuration reloaded successfully"
        assert response.endpoints_count == 5
        assert response.errors == ["Warning: deprecated field"]
    
    def test_reload_response_model_defaults(self):
        """Test ReloadResponse model with defaults."""
        response = ReloadResponse(
            success=False,
            message="Reload failed",
            endpoints_count=0
        )
        
        assert response.success is False
        assert response.message == "Reload failed"
        assert response.endpoints_count == 0
        assert response.errors == []  # Default empty list
    
    def test_config_status_response_model(self):
        """Test ConfigStatusResponse model."""
        response = ConfigStatusResponse(
            loaded=True,
            version="1.2.3",
            config_path="/path/to/config.yaml",
            endpoints_count=10,
            last_reload_error="Some error occurred",
            watching=False
        )
        
        assert response.loaded is True
        assert response.version == "1.2.3"
        assert response.config_path == "/path/to/config.yaml"
        assert response.endpoints_count == 10
        assert response.last_reload_error == "Some error occurred"
        assert response.watching is False
    
    def test_config_status_response_model_optional_fields(self):
        """Test ConfigStatusResponse model with optional fields as None."""
        response = ConfigStatusResponse(
            loaded=False,
            version="0.0.0",
            config_path="",
            endpoints_count=0,
            last_reload_error=None,
            watching=True
        )
        
        assert response.loaded is False
        assert response.last_reload_error is None
        assert response.watching is True


class TestConfigurationAPIIntegration:
    """Integration tests for configuration API."""
    
    def test_configuration_reload_workflow(self, test_app, mock_config_manager):
        """Test complete configuration reload workflow."""
        client = TestClient(test_app)
        
        # Initial config status
        response = client.get("/config/status")
        assert response.status_code == 200
        initial_status = response.json()
        assert initial_status["endpoints_count"] == 1
        
        # Reload configuration with new endpoints
        updated_config = OrchestratorConfig(
            endpoints=[
                EndpointConfig(url="https://api1.example.com", name="api1"),
                EndpointConfig(url="https://api2.example.com", name="api2"),
                EndpointConfig(url="https://api3.example.com", name="api3")
            ]
        )
        mock_config_manager.reload_config = AsyncMock(return_value=updated_config)
        
        # Update status to reflect new config
        mock_config_manager.get_status.return_value = {
            "loaded": True,
            "version": "1.1.0",
            "config_path": "/config/config.yaml",
            "endpoints_count": 3,
            "watching": True,
            "last_reload_error": None
        }
        mock_config_manager.get_config.return_value = updated_config
        
        # Trigger reload
        response = client.post("/config/reload")
        assert response.status_code == 200
        reload_data = response.json()
        assert reload_data["success"] is True
        assert reload_data["endpoints_count"] == 3
        
        # Check updated status
        response = client.get("/config/status")
        assert response.status_code == 200
        updated_status = response.json()
        assert updated_status["endpoints_count"] == 3
        assert updated_status["version"] == "1.1.0"
        
        # List updated endpoints
        response = client.get("/config/endpoints")
        assert response.status_code == 200
        endpoints_data = response.json()
        assert len(endpoints_data["endpoints"]) == 3
        assert endpoints_data["total_count"] == 3
    
    def test_error_handling_consistency(self, test_app, mock_config_manager):
        """Test consistent error handling across endpoints."""
        client = TestClient(test_app)
        
        # Simulate system failure
        system_error = Exception("System unavailable")
        mock_config_manager.get_status.side_effect = system_error
        mock_config_manager.get_config.side_effect = system_error
        mock_config_manager.reload_config = AsyncMock(side_effect=system_error)
        
        # All endpoints should return 500 with consistent error format
        endpoints_to_test = [
            ("GET", "/config/status"),
            ("GET", "/config/endpoints"),
            ("POST", "/config/reload")
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "System unavailable" in data["detail"]
            
    def test_standardized_error_response_format(self, test_app, mock_config_manager):
        """Test that error responses follow standardized format."""
        client = TestClient(test_app)
        
        # Test different types of errors
        test_cases = [
            {
                "error": ValueError("Invalid configuration"),
                "expected_status": 500,
                "expected_message_contains": "Invalid configuration"
            },
            {
                "error": FileNotFoundError("Config file not found"),
                "expected_status": 500,
                "expected_message_contains": "Config file not found"
            },
            {
                "error": PermissionError("Permission denied"),
                "expected_status": 500,
                "expected_message_contains": "Permission denied"
            }
        ]
        
        for test_case in test_cases:
            mock_config_manager.get_status.side_effect = test_case["error"]
            
            response = client.get("/config/status")
            assert response.status_code == test_case["expected_status"]
            
            data = response.json()
            assert "detail" in data
            assert test_case["expected_message_contains"] in data["detail"]
            assert "Failed to get configuration status" in data["detail"]  # Standardized prefix
            
    def test_error_logging_on_exceptions(self, test_app, mock_config_manager):
        """Test that exceptions are properly logged."""
        client = TestClient(test_app)
        
        with patch('src.orchestrator.config_api.logger') as mock_logger:
            mock_config_manager.get_status.side_effect = Exception("Test error")
            
            response = client.get("/config/status")
            assert response.status_code == 500
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args[0][0]
            assert "Failed to get configuration status" in log_call
            assert "Test error" in log_call 