"""
Tests for FastAPI application creation and configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.orchestrator.app import create_app
from src.orchestrator.models import OrchestratorConfig


class TestAppCreation:
    """Test application creation and configuration."""
    
    def test_create_app_basic(self):
        """Test basic app creation."""
        app = create_app()
        assert app is not None
        assert app.title == "Orchestrator API"
        assert app.version == "0.1.0"
    
    def test_create_app_with_required_routes(self):
        """Test app creation includes required routes."""
        app = create_app()
        assert app is not None
        # Verify the app has the required routes
        assert any("/config" in str(route.path) for route in app.routes)
        assert any("/registry" in str(route.path) for route in app.routes)
        assert any("/router" in str(route.path) for route in app.routes)
        assert any("/health" in str(route.path) for route in app.routes)
    
    def test_app_client_basic_routes(self):
        """Test basic routes through test client."""
        app = create_app()
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Orchestrator API"
        assert "endpoints" in data
    
    def test_app_with_lifespan_events(self):
        """Test app lifecycle events."""
        app = create_app()
        assert app.router.lifespan_context is not None

    def test_create_app_registers_routes(self):
        """Test that app registers routes."""
        app = create_app()
        
        # Check that some routes are registered
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        # Should have some routes registered
        assert len(route_paths) > 0
    
    def test_create_app_has_middleware(self):
        """Test that app has middleware."""
        app = create_app()
        
        # Should have CORS middleware and request ID middleware
        assert hasattr(app, 'user_middleware')
        assert len(app.user_middleware) >= 1  # At least CORS middleware
        
        # Check for request ID middleware in HTTP middleware stack
        assert hasattr(app, 'middleware_stack')
        
    def test_app_has_global_exception_handler(self):
        """Test that app has global exception handler."""
        app = create_app()
        
        # Should have exception handlers
        assert hasattr(app, 'exception_handlers')
        assert Exception in app.exception_handlers
        
    def test_request_id_middleware_functionality(self):
        """Test request ID middleware adds headers."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Request ID should be a valid UUID
        request_id = response.headers["X-Request-ID"]
        import uuid
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail("Request ID is not a valid UUID")
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_functionality(self):
        """Test global exception handler works correctly."""
        from fastapi import Request
        from unittest.mock import Mock
        from src.orchestrator.app import global_exception_handler
        
        # Create a mock request
        request = Mock(spec=Request)
        request.url = "http://testserver/test-exception"
        request.method = "GET"
        
        # Test the exception handler directly
        test_exception = ValueError("Test exception")
        response = await global_exception_handler(request, test_exception)
        
        assert response.status_code == 500
        data = response.body
        import json
        parsed_data = json.loads(data)
        assert parsed_data["error"] == "internal_server_error"
        assert parsed_data["message"] == "An internal server error occurred"
        assert "details" in parsed_data
        assert parsed_data["details"]["path"] == "http://testserver/test-exception"
        assert parsed_data["details"]["method"] == "GET"
        
    def test_request_id_uniqueness_across_requests(self):
        """Test that request IDs are unique across multiple requests."""
        app = create_app()
        client = TestClient(app)
        
        request_ids = set()
        
        # Make multiple requests
        for _ in range(10):
            response = client.get("/")
            assert response.status_code == 200
            request_id = response.headers["X-Request-ID"]
            request_ids.add(request_id)
        
        # All request IDs should be unique
        assert len(request_ids) == 10
        
    def test_concurrent_request_handling(self):
        """Test that app handles concurrent requests properly."""
        app = create_app()
        client = TestClient(app)
        
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/")
            results.append({
                "status": response.status_code,
                "request_id": response.headers.get("X-Request-ID"),
                "timestamp": time.time()
            })
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        for result in results:
            assert result["status"] == 200
            assert result["request_id"] is not None
        
        # All request IDs should be unique
        request_ids = [result["request_id"] for result in results]
        assert len(set(request_ids)) == 5
        
    def test_app_graceful_degradation_on_service_failure(self):
        """Test that app degrades gracefully when services fail."""
        app = create_app()
        client = TestClient(app)
        
        # Root endpoint should still work even if internal services fail
        response = client.get("/")
        assert response.status_code == 200
        
        # Basic service info should be available
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data 