"""
Tests for router API endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.orchestrator.router_api import router
from src.orchestrator.router import RequestRouter


@pytest.fixture
def mock_request_router():
    """Mock request router for testing."""
    request_router = MagicMock(spec=RequestRouter)
    
    # Mock sample route data
    sample_routes = [
        {
            "pattern": "/test_api",
            "endpoint_id": "test_api",
            "target_url": "https://api.example.com",
            "methods": ["GET", "POST"],
            "status": "active",
            "circuit_breaker_state": "closed"
        }
    ]
    
    request_router.get_active_routes.return_value = sample_routes
    request_router.test_endpoint_connectivity = AsyncMock(return_value={
        "endpoint_id": "test_api",
        "url": "https://api.example.com",
        "status_code": 200,
        "response_time": 0.1,
        "success": True,
        "error": None
    })
    request_router.refresh_routes.return_value = None
    
    return request_router


@pytest.fixture
def test_app(mock_request_router):
    """Test FastAPI application with router API."""
    app = FastAPI()
    
    # Mock the dependency
    def get_mock_request_router():
        return mock_request_router
    
    # Override the dependency
    from src.orchestrator.router_api import get_router
    app.dependency_overrides[get_router] = get_mock_request_router
    
    # Include the router
    app.include_router(router)
    
    return app


class TestRouterAPI:
    """Test router API endpoints."""
    
    def test_list_active_routes_success(self, test_app, mock_request_router):
        """Test listing active routes successfully."""
        # Mock multiple routes
        routes = [
            {
                "pattern": "/api1",
                "endpoint_id": "api1",
                "target_url": "https://api1.example.com",
                "methods": ["GET", "POST"],
                "status": "active",
                "circuit_breaker_state": "closed"
            },
            {
                "pattern": "/api2",
                "endpoint_id": "api2",
                "target_url": "https://api2.example.com",
                "methods": ["GET"],
                "status": "active",
                "circuit_breaker_state": "closed"
            }
        ]
        
        mock_request_router.get_active_routes.return_value = routes
        
        client = TestClient(test_app)
        response = client.get("/router/routes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "routes" in data
        assert len(data["routes"]) == 2
        assert data["total_count"] == 2
        assert "timestamp" in data
        
        # Check first route
        route1 = data["routes"][0]
        assert route1["endpoint_id"] == "api1"
        assert route1["target_url"] == "https://api1.example.com"
        assert route1["methods"] == ["GET", "POST"]
        assert route1["status"] == "active"
        
        # Check second route
        route2 = data["routes"][1]
        assert route2["endpoint_id"] == "api2"
        assert route2["target_url"] == "https://api2.example.com"
        assert route2["methods"] == ["GET"]
        assert route2["status"] == "active"
    
    def test_list_active_routes_empty(self, test_app, mock_request_router):
        """Test listing active routes when none exist."""
        mock_request_router.get_active_routes.return_value = []
        
        client = TestClient(test_app)
        response = client.get("/router/routes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["routes"] == []
        assert data["total_count"] == 0
        assert "timestamp" in data
    
    def test_list_active_routes_failure(self, test_app, mock_request_router):
        """Test listing active routes with failure."""
        mock_request_router.get_active_routes.side_effect = Exception("Router error")
        
        client = TestClient(test_app)
        response = client.get("/router/routes")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to list active routes" in data["detail"]
        assert "Router error" in data["detail"]
    
    def test_test_endpoint_connectivity_success(self, test_app, mock_request_router):
        """Test endpoint connectivity test successfully."""
        connectivity_result = {
            "endpoint_id": "test_endpoint",
            "url": "https://api.example.com",
            "status_code": 200,
            "response_time": 0.05,
            "success": True,
            "error": None
        }
        mock_request_router.test_endpoint_connectivity.return_value = connectivity_result
        
        client = TestClient(test_app)
        response = client.get("/router/test/test_endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "test_result" in data
        test_result = data["test_result"]
        assert test_result["endpoint_id"] == "test_endpoint"
        assert test_result["status_code"] == 200
        assert test_result["response_time"] == 0.05
        assert test_result["success"] is True
        assert "timestamp" in data
        
        # Verify connectivity test was called
        mock_request_router.test_endpoint_connectivity.assert_called_once_with("test_endpoint")
    
    def test_test_endpoint_connectivity_failure(self, test_app, mock_request_router):
        """Test endpoint connectivity test with failure."""
        connectivity_result = {
            "endpoint_id": "failing_endpoint",
            "url": "https://api.example.com",
            "status_code": None,
            "response_time": 10.0,
            "success": False,
            "error": "Connection timeout"
        }
        mock_request_router.test_endpoint_connectivity.return_value = connectivity_result
        
        client = TestClient(test_app)
        response = client.get("/router/test/failing_endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "test_result" in data
        test_result = data["test_result"]
        assert test_result["success"] is False
        assert test_result["error"] == "Connection timeout"
        assert "timestamp" in data
    
    def test_test_endpoint_connectivity_not_found(self, test_app, mock_request_router):
        """Test endpoint connectivity test for non-existent endpoint."""
        mock_request_router.test_endpoint_connectivity.side_effect = ValueError("Endpoint not found: nonexistent")
        
        client = TestClient(test_app)
        response = client.get("/router/test/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["detail"] == "Endpoint not found: nonexistent"
    
    def test_test_endpoint_connectivity_exception(self, test_app, mock_request_router):
        """Test endpoint connectivity test with exception."""
        mock_request_router.test_endpoint_connectivity.side_effect = Exception("Connectivity test failed")
        
        client = TestClient(test_app)
        response = client.get("/router/test/test_endpoint")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to test endpoint connectivity" in data["detail"]
        assert "Connectivity test failed" in data["detail"]
    
    def test_refresh_route_mappings_success(self, test_app, mock_request_router):
        """Test refreshing route mappings successfully."""
        # Mock refreshed routes
        refreshed_routes = [
            {
                "pattern": "/updated_api",
                "endpoint_id": "updated_api",
                "target_url": "https://updated.example.com",
                "methods": ["GET"],
                "status": "active",
                "circuit_breaker_state": "closed"
            }
        ]
        mock_request_router.get_active_routes.return_value = refreshed_routes
        
        client = TestClient(test_app)
        response = client.post("/router/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Route mappings refreshed successfully"
        assert data["active_routes_count"] == 1
        assert "timestamp" in data
        
        # Verify refresh was called
        mock_request_router.refresh_routes.assert_called_once()
        mock_request_router.get_active_routes.assert_called()
    
    def test_refresh_route_mappings_failure(self, test_app, mock_request_router):
        """Test refreshing route mappings with failure."""
        mock_request_router.refresh_routes.side_effect = Exception("Refresh failed")
        
        client = TestClient(test_app)
        response = client.post("/router/refresh")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to refresh route mappings" in data["detail"]
        assert "Refresh failed" in data["detail"]


class TestRouterAPIIntegration:
    """Integration tests for router API."""
    
    def test_route_management_workflow(self, test_app, mock_request_router):
        """Test complete route management workflow."""
        client = TestClient(test_app)
        
        # Step 1: List initial routes
        response = client.get("/router/routes")
        assert response.status_code == 200
        initial_data = response.json()
        
        # Step 2: Test endpoint connectivity
        response = client.get("/router/test/test_endpoint")
        assert response.status_code == 200
        connectivity_data = response.json()
        assert "test_result" in connectivity_data
        
        # Step 3: Refresh routes
        response = client.post("/router/refresh")
        assert response.status_code == 200
        refresh_data = response.json()
        assert refresh_data["success"] is True
        
        # Step 4: List routes again
        response = client.get("/router/routes")
        assert response.status_code == 200
        final_data = response.json()
        
        # Verify all operations completed successfully
        assert "routes" in initial_data
        assert "routes" in final_data
    
    def test_error_handling_consistency(self, test_app, mock_request_router):
        """Test consistent error handling across endpoints."""
        # Mock various failures
        mock_request_router.get_active_routes.side_effect = Exception("Routes error")
        mock_request_router.test_endpoint_connectivity.side_effect = Exception("Connectivity error")
        mock_request_router.refresh_routes.side_effect = Exception("Refresh error")
        
        client = TestClient(test_app)
        
        # Test routes endpoint error
        response = client.get("/router/routes")
        assert response.status_code == 500
        assert "Failed to list active routes" in response.json()["detail"]
        
        # Test connectivity endpoint error
        response = client.get("/router/test/test_endpoint")
        assert response.status_code == 500
        assert "Failed to test endpoint connectivity" in response.json()["detail"]
        
        # Test refresh endpoint error
        response = client.post("/router/refresh")
        assert response.status_code == 500
        assert "Failed to refresh route mappings" in response.json()["detail"] 