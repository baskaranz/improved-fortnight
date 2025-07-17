"""
Tests for middleware functionality including logging and security headers.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from src.orchestrator.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware functionality."""
    
    @pytest.mark.asyncio
    async def test_middleware_adds_request_id(self, test_app):
        """Test middleware adds request ID to response headers."""
        middleware = RequestLoggingMiddleware(test_app)
        
        # Mock request and response
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/test"
        request.state = MagicMock()
        
        response = Response("OK")
        
        async def mock_call_next(req):
            return response
        
        result = await middleware.dispatch(request, mock_call_next)
        
        # Check that request ID was added to response headers
        assert "X-Request-ID" in result.headers
        assert "X-Response-Time" in result.headers
        
        # Check that request ID was set on request state
        assert hasattr(request.state, 'request_id')
    
    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self, test_app):
        """Test middleware handles exceptions properly."""
        middleware = RequestLoggingMiddleware(test_app)
        
        # Mock request
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/test"
        request.state = MagicMock()
        
        async def mock_call_next_with_error(req):
            raise ValueError("Test error")
        
        # Exception should be re-raised
        with pytest.raises(ValueError, match="Test error"):
            await middleware.dispatch(request, mock_call_next_with_error)
        
        # But request ID should still be set
        assert hasattr(request.state, 'request_id')


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware functionality."""
    
    @pytest.mark.asyncio
    async def test_middleware_adds_security_headers(self, test_app):
        """Test middleware adds security headers."""
        middleware = SecurityHeadersMiddleware(test_app)
        
        # Mock request
        request = MagicMock()
        
        response = Response("OK")
        
        async def mock_call_next(req):
            return response
        
        result = await middleware.dispatch(request, mock_call_next)
        
        # Check that security headers were added
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        for header in expected_headers:
            assert header in result.headers
        
        # Check specific header values
        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert result.headers["X-XSS-Protection"] == "1; mode=block"
    
    @pytest.mark.asyncio
    async def test_middleware_preserves_existing_headers(self, test_app):
        """Test middleware preserves existing response headers."""
        middleware = SecurityHeadersMiddleware(test_app)
        
        # Mock request
        request = MagicMock()
        
        response = Response("OK")
        response.headers["Custom-Header"] = "custom-value"
        
        async def mock_call_next(req):
            return response
        
        result = await middleware.dispatch(request, mock_call_next)
        
        # Check that custom header is preserved
        assert result.headers["Custom-Header"] == "custom-value"
        
        # Check that security headers were still added
        assert "X-Content-Type-Options" in result.headers


class TestMiddlewareStack:
    """Test multiple middleware together."""
    
    @pytest.mark.asyncio
    async def test_multiple_middleware_stack(self):
        """Test multiple middleware working together."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Add both middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestLoggingMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check that both middleware effects are present
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Content-Type-Options" in response.headers
        
    def test_middleware_compatibility_with_app_request_id(self):
        """Test middleware compatibility with app-level request ID handling."""
        from src.orchestrator.app import add_request_id_header
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Add app-level request ID handler
        app.middleware("http")(add_request_id_header)
        
        # Add other middleware
        app.add_middleware(SecurityHeadersMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Should have request ID from app-level handler
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Content-Type-Options" in response.headers
        
        # Verify request ID is a valid UUID
        import uuid
        try:
            uuid.UUID(response.headers["X-Request-ID"])
        except ValueError:
            pytest.fail("Request ID is not a valid UUID") 