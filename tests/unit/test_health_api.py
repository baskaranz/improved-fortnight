"""
Tests for health monitoring API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from datetime import datetime

from src.orchestrator.health_api import router
from src.orchestrator.health import HealthChecker
from src.orchestrator.circuit_breaker import CircuitBreakerManager
from src.orchestrator.models import EndpointHealth, EndpointStatus


@pytest.fixture
def mock_health_checker():
    """Mock health checker for testing."""
    health_checker = MagicMock(spec=HealthChecker)
    
    # Mock health data
    sample_health = EndpointHealth(
        endpoint_id="test_endpoint",
        status=EndpointStatus.ACTIVE,
        last_check_time=datetime.now(),
        response_time=0.05,
        error_message=None,
        consecutive_failures=0,
        consecutive_successes=5
    )
    
    health_checker.get_all_health_status.return_value = [sample_health]
    health_checker.get_endpoint_health.return_value = sample_health
    health_checker.get_unhealthy_endpoints.return_value = []
    health_checker.force_health_check = AsyncMock(return_value=None)
    
    return health_checker


@pytest.fixture
def mock_circuit_breaker_manager():
    """Mock circuit breaker manager for testing."""
    cb_manager = MagicMock(spec=CircuitBreakerManager)
    
    # Mock circuit breaker stats
    sample_cb_stats = {
        "endpoint_id": "test_endpoint",
        "state": "closed",
        "failure_count": 0,
        "last_failure_time": None,
        "last_success_time": datetime.now().isoformat(),
        "state_changed_time": datetime.now().isoformat(),
        "half_open_calls": 0
    }
    
    cb_manager.get_all_circuit_breaker_stats.return_value = [sample_cb_stats]
    cb_manager.get_circuit_breaker_stats.return_value = sample_cb_stats
    
    return cb_manager


@pytest.fixture
def test_app(mock_health_checker, mock_circuit_breaker_manager):
    """Test FastAPI application with health API."""
    app = FastAPI()
    
    # Mock the dependencies
    def get_mock_health_checker():
        return mock_health_checker
    
    def get_mock_circuit_breaker_manager():
        return mock_circuit_breaker_manager
    
    # Override the dependencies
    from src.orchestrator.health_api import get_health_checker, get_circuit_breaker_manager
    app.dependency_overrides[get_health_checker] = get_mock_health_checker
    app.dependency_overrides[get_circuit_breaker_manager] = get_mock_circuit_breaker_manager
    
    # Include the router
    app.include_router(router)
    
    return app


class TestHealthAPI:
    """Test health monitoring API endpoints."""
    
    def test_get_all_endpoints_health_success(self, test_app, mock_health_checker):
        """Test getting all endpoints health successfully."""
        # Mock multiple health statuses
        health_data = [
            EndpointHealth(
                endpoint_id="api1",
                status=EndpointStatus.ACTIVE,
                last_check_time=datetime(2023, 1, 1, 12, 0),
                response_time=0.05,
                error_message=None,
                consecutive_failures=0,
                consecutive_successes=10
            ),
            EndpointHealth(
                endpoint_id="api2",
                status=EndpointStatus.UNHEALTHY,
                last_check_time=datetime(2023, 1, 1, 12, 5),
                response_time=2.0,
                error_message="Connection timeout",
                consecutive_failures=3,
                consecutive_successes=0
            )
        ]
        mock_health_checker.get_all_health_status.return_value = health_data
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert len(data["endpoints"]) == 2
        assert data["total_count"] == 2
        assert "timestamp" in data
        
        # Check first endpoint health
        endpoint1 = data["endpoints"][0]
        assert endpoint1["endpoint_id"] == "api1"
        assert endpoint1["status"] == "active"
        assert endpoint1["response_time"] == 0.05
        assert endpoint1["error_message"] is None
        assert endpoint1["consecutive_failures"] == 0
        assert endpoint1["consecutive_successes"] == 10
        
        # Check second endpoint health
        endpoint2 = data["endpoints"][1]
        assert endpoint2["endpoint_id"] == "api2"
        assert endpoint2["status"] == "unhealthy"
        assert endpoint2["response_time"] == 2.0
        assert endpoint2["error_message"] == "Connection timeout"
        assert endpoint2["consecutive_failures"] == 3
        assert endpoint2["consecutive_successes"] == 0
    
    def test_get_all_endpoints_health_empty(self, test_app, mock_health_checker):
        """Test getting all endpoints health when none exist."""
        mock_health_checker.get_all_health_status.return_value = []
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoints"] == []
        assert data["total_count"] == 0
        assert "timestamp" in data
    
    def test_get_all_endpoints_health_failure(self, test_app, mock_health_checker):
        """Test getting all endpoints health with failure."""
        mock_health_checker.get_all_health_status.side_effect = Exception("Health check failed")
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to get endpoints health" in data["detail"]
        assert "Health check failed" in data["detail"]
    
    def test_get_endpoint_health_success(self, test_app, mock_health_checker):
        """Test getting specific endpoint health successfully."""
        endpoint_health = EndpointHealth(
            endpoint_id="specific_endpoint",
            status=EndpointStatus.INACTIVE,
            last_check_time=datetime(2023, 1, 1, 12, 30),
            response_time=1.5,
            error_message="Slow response",
            consecutive_failures=1,
            consecutive_successes=2
        )
        mock_health_checker.get_endpoint_health.return_value = endpoint_health
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints/specific_endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["endpoint_id"] == "specific_endpoint"
        assert data["status"] == "inactive"
        assert data["response_time"] == 1.5
        assert data["error_message"] == "Slow response"
        assert data["consecutive_failures"] == 1
        assert data["consecutive_successes"] == 2
        assert "timestamp" in data
    
    def test_get_endpoint_health_not_found(self, test_app, mock_health_checker):
        """Test getting health for non-existent endpoint."""
        mock_health_checker.get_endpoint_health.return_value = None
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"] == "Health data not found for endpoint: nonexistent"
    
    def test_get_endpoint_health_failure(self, test_app, mock_health_checker):
        """Test getting endpoint health with failure."""
        mock_health_checker.get_endpoint_health.side_effect = Exception("Health lookup failed")
        
        client = TestClient(test_app)
        response = client.get("/health/endpoints/test_endpoint")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to get endpoint health" in data["detail"]
        assert "Health lookup failed" in data["detail"]
    
    def test_trigger_immediate_health_check_success(self, test_app, mock_health_checker):
        """Test triggering immediate health check successfully."""
        mock_health = EndpointHealth(
            endpoint_id="test_endpoint",
            status=EndpointStatus.ACTIVE,
            last_check_time=datetime(2023, 1, 1, 12, 0),
            response_time=0.15,
            error_message=None,
            consecutive_failures=0,
            consecutive_successes=5
        )
        mock_health_checker.check_endpoint_immediately.return_value = mock_health
        
        client = TestClient(test_app)
        response = client.post("/health/check/test_endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Health check completed for test_endpoint"
        assert "result" in data
        assert data["result"]["endpoint_id"] == "test_endpoint"
        assert data["result"]["status"] == "active"
        assert "timestamp" in data
        
        # Verify immediate check was called
        mock_health_checker.check_endpoint_immediately.assert_called_once_with("test_endpoint")
    
    def test_trigger_immediate_health_check_failure(self, test_app, mock_health_checker):
        """Test triggering immediate health check with failure."""
        mock_health_checker.check_endpoint_immediately.side_effect = Exception("Check failed")
        
        client = TestClient(test_app)
        response = client.post("/health/check/test_endpoint")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to trigger health check" in data["detail"]
        assert "Check failed" in data["detail"]
    
    def test_get_unhealthy_endpoints_success(self, test_app, mock_health_checker):
        """Test getting unhealthy endpoints successfully."""
        unhealthy_data = [
            EndpointHealth(
                endpoint_id="failing_api",
                status=EndpointStatus.UNHEALTHY,
                last_check_time=datetime(2023, 1, 1, 12, 0),
                response_time=None,
                error_message="Service unavailable",
                consecutive_failures=5,
                consecutive_successes=0
            ),
            EndpointHealth(
                endpoint_id="slow_api",
                status=EndpointStatus.DISABLED,
                last_check_time=datetime(2023, 1, 1, 12, 5),
                response_time=3.0,
                error_message="Timeout warning",
                consecutive_failures=2,
                consecutive_successes=1
            )
        ]
        mock_health_checker.get_unhealthy_endpoints.return_value = unhealthy_data
        
        client = TestClient(test_app)
        response = client.get("/health/unhealthy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "unhealthy_endpoints" in data
        assert len(data["unhealthy_endpoints"]) == 2
        assert data["count"] == 2
        assert "timestamp" in data
        
        # Check endpoints details
        endpoint1 = data["unhealthy_endpoints"][0]
        assert endpoint1["endpoint_id"] == "failing_api"
        assert endpoint1["status"] == "unhealthy"
        assert endpoint1["error_message"] == "Service unavailable"
        
        endpoint2 = data["unhealthy_endpoints"][1]
        assert endpoint2["endpoint_id"] == "slow_api"
        assert endpoint2["status"] == "disabled"
        assert endpoint2["error_message"] == "Timeout warning"
    
    def test_get_unhealthy_endpoints_empty(self, test_app, mock_health_checker):
        """Test getting unhealthy endpoints when all are healthy."""
        mock_health_checker.get_unhealthy_endpoints.return_value = []
        
        client = TestClient(test_app)
        response = client.get("/health/unhealthy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["unhealthy_endpoints"] == []
        assert data["count"] == 0
        assert "timestamp" in data
    
    def test_get_unhealthy_endpoints_failure(self, test_app, mock_health_checker):
        """Test getting unhealthy endpoints with failure."""
        mock_health_checker.get_unhealthy_endpoints.side_effect = Exception("Unhealthy lookup failed")
        
        client = TestClient(test_app)
        response = client.get("/health/unhealthy")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to get unhealthy endpoints" in data["detail"]
        assert "Unhealthy lookup failed" in data["detail"]


class TestHealthAPIIntegration:
    """Integration tests for health API."""
    
    def test_health_monitoring_workflow(self, test_app, mock_health_checker):
        """Test complete health monitoring workflow."""
        client = TestClient(test_app)
        
        # Initial health check - all healthy
        healthy_data = [
            EndpointHealth(
                endpoint_id="api1",
                status=EndpointStatus.ACTIVE,
                last_check_time=datetime(2023, 1, 1, 10, 0),
                response_time=0.1,
                error_message=None,
                consecutive_failures=0,
                consecutive_successes=10
            ),
            EndpointHealth(
                endpoint_id="api2",
                status=EndpointStatus.ACTIVE,
                last_check_time=datetime(2023, 1, 1, 10, 0),
                response_time=0.2,
                error_message=None,
                consecutive_failures=0,
                consecutive_successes=8
            )
        ]
        mock_health_checker.get_all_health_status.return_value = healthy_data
        mock_health_checker.get_unhealthy_endpoints.return_value = []
        
        # Get all endpoints - should be healthy
        response = client.get("/health/endpoints")
        assert response.status_code == 200
        data = response.json()
        assert len(data["endpoints"]) == 2
        assert all(ep["status"] == "active" for ep in data["endpoints"])
        
        # Check unhealthy endpoints - should be empty
        response = client.get("/health/unhealthy")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        
        # Simulate one endpoint becoming unhealthy
        unhealthy_data = [
            EndpointHealth(
                endpoint_id="api1",
                status=EndpointStatus.ACTIVE,
                last_check_time=datetime(2023, 1, 1, 11, 0),
                response_time=0.1,
                error_message=None,
                consecutive_failures=0,
                consecutive_successes=15
            ),
            EndpointHealth(
                endpoint_id="api2",
                status=EndpointStatus.UNHEALTHY,
                last_check_time=datetime(2023, 1, 1, 11, 0),
                response_time=None,
                error_message="Connection refused",
                consecutive_failures=3,
                consecutive_successes=0
            )
        ]
        mock_health_checker.get_all_health_status.return_value = unhealthy_data
        mock_health_checker.get_unhealthy_endpoints.return_value = [unhealthy_data[1]]
        
        # Force a health check for api2
        mock_health_checker.check_endpoint_immediately.return_value = unhealthy_data[1]
        response = client.post("/health/check/api2")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Check updated status
        response = client.get("/health/endpoints")
        assert response.status_code == 200
        data = response.json()
        statuses = {ep["endpoint_id"]: ep["status"] for ep in data["endpoints"]}
        assert statuses["api1"] == "active"
        assert statuses["api2"] == "unhealthy"
        
        # Check unhealthy endpoints
        response = client.get("/health/unhealthy")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["unhealthy_endpoints"][0]["endpoint_id"] == "api2"
        
        # Check specific endpoint
        mock_health_checker.get_endpoint_health.return_value = unhealthy_data[1]
        response = client.get("/health/endpoints/api2")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["error_message"] == "Connection refused"
    
    def test_error_handling_consistency(self, test_app, mock_health_checker):
        """Test consistent error handling across health endpoints."""
        client = TestClient(test_app)
        
        # Simulate system failure
        system_error = Exception("Health system unavailable")
        mock_health_checker.get_all_health_status.side_effect = system_error
        mock_health_checker.get_endpoint_health.side_effect = system_error
        mock_health_checker.get_unhealthy_endpoints.side_effect = system_error
        mock_health_checker.check_endpoint_immediately.side_effect = system_error
        
        # All endpoints should return 500 with consistent error format
        endpoints_to_test = [
            ("GET", "/health/endpoints"),
            ("GET", "/health/endpoints/test_endpoint"),
            ("GET", "/health/unhealthy"),
            ("POST", "/health/check/test_endpoint")
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Health system unavailable" in data["detail"] or "unavailable" in data["detail"].lower() 