"""
Unit tests for request router.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, Response, HTTPException
import httpx

from src.orchestrator.router import EndpointProxy, RequestRouter
from src.orchestrator.registry import EndpointRegistry
from src.orchestrator.models import (
    EndpointConfig,
    RegisteredEndpoint,
    EndpointStatus,
    CircuitBreakerState,
    HTTPMethod,
    AuthType
)


@pytest.fixture
def registry():
    """Create a test registry."""
    return EndpointRegistry()


@pytest.fixture
def sample_endpoint_config():
    """Create a sample endpoint configuration."""
    return EndpointConfig(
        url="https://api.example.com/v1",
        name="test_api",
        version="v1",
        methods=[HTTPMethod.GET, HTTPMethod.POST],
        auth_type=AuthType.NONE,
        timeout=30
    )


@pytest.fixture
def registered_endpoint(registry, sample_endpoint_config):
    """Create a registered endpoint."""
    return registry.register_endpoint(sample_endpoint_config)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.method = "GET"
    request.headers = {"host": "localhost", "user-agent": "test"}
    request.query_params = {}
    request.body = AsyncMock(return_value=b"")
    return request


class TestEndpointProxy:
    """Test cases for EndpointProxy."""
    
    def test_endpoint_proxy_initialization(self):
        """Test endpoint proxy initialization."""
        proxy = EndpointProxy(timeout=60)
        assert proxy.timeout == 60
        assert proxy.client is not None
    
    def test_endpoint_proxy_default_timeout(self):
        """Test endpoint proxy with default timeout."""
        proxy = EndpointProxy()
        assert proxy.timeout == 30
    
    @pytest.mark.asyncio
    async def test_forward_request_success(self, registered_endpoint, mock_request):
        """Test successful request forwarding."""
        proxy = EndpointProxy()
        
        # Mock the HTTP client response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.content = b'{"status": "ok"}'
        
        with patch.object(proxy.client, 'request', new_callable=AsyncMock) as mock_client:
            mock_client.return_value = mock_response
            
            status_code, headers, content = await proxy.forward_request(
                registered_endpoint, mock_request, "test/path"
            )
            
            assert status_code == 200
            assert "content-type" in headers
            assert content == b'{"status": "ok"}'
            assert "X-Orchestrated-By" in headers
            
            # Verify client was called with correct parameters
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert call_args[1]["method"] == "GET"
            assert "test/path" in call_args[1]["url"]
    
    @pytest.mark.asyncio
    async def test_forward_request_with_path(self, registered_endpoint, mock_request):
        """Test request forwarding with additional path."""
        proxy = EndpointProxy()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'{"result": "success"}'
        
        with patch.object(proxy.client, 'request', new_callable=AsyncMock) as mock_client:
            mock_client.return_value = mock_response
            
            await proxy.forward_request(registered_endpoint, mock_request, "/api/data")
            
            call_args = mock_client.call_args
            # Path should be properly joined with base URL
            assert "/api/data" in call_args[1]["url"]
    
    @pytest.mark.asyncio
    async def test_forward_request_timeout(self, registered_endpoint, mock_request):
        """Test request forwarding with timeout exception."""
        proxy = EndpointProxy()
        
        with patch.object(proxy.client, 'request', new_callable=AsyncMock) as mock_client:
            mock_client.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(HTTPException) as exc_info:
                await proxy.forward_request(registered_endpoint, mock_request)
            
            assert exc_info.value.status_code == 504
            assert "timeout" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_forward_request_connection_error(self, registered_endpoint, mock_request):
        """Test request forwarding with connection error."""
        proxy = EndpointProxy()
        
        with patch.object(proxy.client, 'request', new_callable=AsyncMock) as mock_client:
            mock_client.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(HTTPException) as exc_info:
                await proxy.forward_request(registered_endpoint, mock_request)
            
            assert exc_info.value.status_code == 502
            assert "connection error" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_forward_request_generic_error(self, registered_endpoint, mock_request):
        """Test request forwarding with generic error."""
        proxy = EndpointProxy()
        
        with patch.object(proxy.client, 'request', new_callable=AsyncMock) as mock_client:
            mock_client.side_effect = Exception("Generic error")
            
            with pytest.raises(HTTPException) as exc_info:
                await proxy.forward_request(registered_endpoint, mock_request)
            
            assert exc_info.value.status_code == 502
            assert "Orchestration error" in str(exc_info.value.detail)
    
    def test_filter_headers(self):
        """Test header filtering for requests."""
        proxy = EndpointProxy()
        
        headers = {
            "host": "example.com",
            "connection": "keep-alive",
            "user-agent": "test-agent",
            "authorization": "Bearer token",
            "proxy-connection": "keep-alive",
            "custom-header": "value"
        }
        
        filtered = proxy._filter_headers(headers)
        
        # Should remove hop-by-hop headers
        assert "host" not in filtered
        assert "connection" not in filtered
        assert "proxy-connection" not in filtered
        
        # Should keep other headers
        assert filtered["user-agent"] == "test-agent"
        assert filtered["authorization"] == "Bearer token"
        assert filtered["custom-header"] == "value"
    
    def test_filter_response_headers(self):
        """Test header filtering for responses."""
        proxy = EndpointProxy()
        
        headers = {
            "content-type": "application/json",
            "connection": "close",
            "server": "nginx/1.0",
            "transfer-encoding": "chunked",
            "custom-response": "value"
        }
        
        filtered = proxy._filter_response_headers(headers)
        
        # Should remove excluded headers
        assert "connection" not in filtered
        assert "server" not in filtered
        assert "transfer-encoding" not in filtered
        
        # Should keep other headers
        assert filtered["content-type"] == "application/json"
        assert filtered["custom-response"] == "value"
        
        # Should add orchestrator header
        assert filtered["X-Orchestrated-By"] == "Orchestrator-API"
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the proxy client."""
        proxy = EndpointProxy()
        
        with patch.object(proxy.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await proxy.close()
            mock_close.assert_called_once()


class TestRequestRouter:
    """Test cases for RequestRouter."""
    
    def test_request_router_initialization(self, registry):
        """Test request router initialization."""
        router = RequestRouter(registry)
        
        assert router.registry is registry
        assert router.proxy is not None
        assert isinstance(router.route_cache, dict)
    
    def test_update_cache(self, registry, sample_endpoint_config):
        """Test route cache updating."""
        router = RequestRouter(registry)
        
        # Register an endpoint
        registry.register_endpoint(sample_endpoint_config)
        
        # Update cache
        router._update_cache()
        
        # Should have route in cache
        assert "/test_api" in router.route_cache
        assert "/v1/test_api" in router.route_cache
    
    def test_update_cache_no_name(self, registry):
        """Test route cache updating with endpoint without name."""
        router = RequestRouter(registry)
        
        # Register endpoint without name
        config = EndpointConfig(url="https://api.example.com")
        registry.register_endpoint(config)
        
        router._update_cache()
        
        # Should not add routes for endpoints without names
        assert len(router.route_cache) == 0
    
    def test_find_endpoint_for_path_exact_match(self, registry, sample_endpoint_config):
        """Test finding endpoint with exact path match."""
        router = RequestRouter(registry)
        registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        endpoint = router._find_endpoint_for_path("/test_api")
        assert endpoint is not None
        assert endpoint.config.name == "test_api"
    
    def test_find_endpoint_for_path_versioned(self, registry, sample_endpoint_config):
        """Test finding endpoint with versioned path."""
        router = RequestRouter(registry)
        registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        endpoint = router._find_endpoint_for_path("/v1/test_api")
        assert endpoint is not None
        assert endpoint.config.name == "test_api"
    
    def test_find_endpoint_for_path_with_subpath(self, registry, sample_endpoint_config):
        """Test finding endpoint with additional path segments."""
        router = RequestRouter(registry)
        registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        endpoint = router._find_endpoint_for_path("/test_api/users/123")
        assert endpoint is not None
        assert endpoint.config.name == "test_api"
    
    def test_find_endpoint_for_path_not_found(self, registry):
        """Test finding endpoint that doesn't exist."""
        router = RequestRouter(registry)
        
        endpoint = router._find_endpoint_for_path("/nonexistent")
        assert endpoint is None
    
    def test_extract_relative_path_basic(self, registry, sample_endpoint_config):
        """Test extracting relative path from full path."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        relative_path = router._extract_relative_path("/test_api/users/123", endpoint)
        assert relative_path == "users/123"
    
    def test_extract_relative_path_versioned(self, registry, sample_endpoint_config):
        """Test extracting relative path from versioned path."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        relative_path = router._extract_relative_path("/v1/test_api/users/123", endpoint)
        assert relative_path == "users/123"
    
    def test_extract_relative_path_exact_match(self, registry, sample_endpoint_config):
        """Test extracting relative path when path exactly matches endpoint."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        relative_path = router._extract_relative_path("/test_api", endpoint)
        assert relative_path == ""
    
    @pytest.mark.asyncio
    async def test_route_request_success(self, registry, sample_endpoint_config, mock_request):
        """Test successful request routing."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        # Mock the proxy forward_request method
        with patch.object(router.proxy, 'forward_request', new_callable=AsyncMock) as mock_forward:
            mock_forward.return_value = (200, {"content-type": "application/json"}, b'{"result": "ok"}')
            
            with patch('time.time', return_value=1000.0):
                response = await router.route_request(mock_request, "/test_api/users")
                
                assert isinstance(response, Response)
                assert response.status_code == 200
                assert response.body == b'{"result": "ok"}'
                assert "X-Response-Time" in response.headers
                assert "X-Endpoint-ID" in response.headers
                
                # Verify success was recorded
                assert endpoint.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_route_request_endpoint_not_found(self, registry, mock_request):
        """Test routing request to non-existent endpoint."""
        router = RequestRouter(registry)
        
        with pytest.raises(HTTPException) as exc_info:
            await router.route_request(mock_request, "/nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "No endpoint found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_route_request_endpoint_disabled(self, registry, mock_request):
        """Test routing request to disabled endpoint."""
        router = RequestRouter(registry)
        
        # Create disabled endpoint
        disabled_config = EndpointConfig(
            url="https://api.example.com",
            name="disabled_api",
            disabled=True
        )
        registry.register_endpoint(disabled_config)
        router._update_cache()
        
        # Disabled endpoints are not added to cache, so they return 404
        with pytest.raises(HTTPException) as exc_info:
            await router.route_request(mock_request, "/disabled_api")
        
        assert exc_info.value.status_code == 404
        assert "No endpoint found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_route_request_endpoint_unhealthy(self, registry, sample_endpoint_config, mock_request):
        """Test routing request to unhealthy endpoint."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        # Make endpoint unhealthy
        endpoint.status = EndpointStatus.UNHEALTHY
        
        with pytest.raises(HTTPException) as exc_info:
            await router.route_request(mock_request, "/test_api")
        
        assert exc_info.value.status_code == 503
        assert "unhealthy" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_route_request_circuit_breaker_open(self, registry, sample_endpoint_config, mock_request):
        """Test routing request when circuit breaker is open."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        # Open circuit breaker
        endpoint.circuit_breaker_state = CircuitBreakerState.OPEN
        
        with pytest.raises(HTTPException) as exc_info:
            await router.route_request(mock_request, "/test_api")
        
        assert exc_info.value.status_code == 503
        assert "circuit breaker" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_route_request_method_not_allowed(self, registry, sample_endpoint_config, mock_request):
        """Test routing request with disallowed HTTP method."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        # Set method to something not allowed
        mock_request.method = "DELETE"
        
        with pytest.raises(HTTPException) as exc_info:
            await router.route_request(mock_request, "/test_api")
        
        assert exc_info.value.status_code == 405
        assert "not allowed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_route_request_proxy_failure(self, registry, sample_endpoint_config, mock_request):
        """Test routing request when proxy fails."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        router._update_cache()
        
        # Mock proxy to raise exception
        with patch.object(router.proxy, 'forward_request', new_callable=AsyncMock) as mock_forward:
            mock_forward.side_effect = HTTPException(status_code=502, detail="Proxy failed")
            
            with pytest.raises(HTTPException) as exc_info:
                await router.route_request(mock_request, "/test_api")
            
            assert exc_info.value.status_code == 502
            # Verify failure was recorded
            assert endpoint.consecutive_failures > 0
    
    def test_refresh_routes(self, registry, sample_endpoint_config):
        """Test refreshing routes."""
        router = RequestRouter(registry)
        
        # Initially empty cache
        assert len(router.route_cache) == 0
        
        # Add endpoint and refresh
        registry.register_endpoint(sample_endpoint_config)
        router.refresh_routes()
        
        # Cache should be updated
        assert len(router.route_cache) > 0
        assert "/test_api" in router.route_cache
    
    def test_get_active_routes(self, registry, sample_endpoint_config):
        """Test getting active routes."""
        router = RequestRouter(registry)
        registry.register_endpoint(sample_endpoint_config)
        router.refresh_routes()
        
        routes = router.get_active_routes()
        
        assert isinstance(routes, list)
        assert len(routes) > 0
        
        # Should contain route info as dicts
        route_patterns = [route["pattern"] for route in routes]
        assert "/test_api" in route_patterns
    
    @pytest.mark.asyncio
    async def test_test_endpoint_connectivity_success(self, registry, sample_endpoint_config):
        """Test endpoint connectivity testing - success case."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        # Mock successful HTTP request
        with patch.object(router.proxy.client, 'get', new_callable=AsyncMock) as mock_get:
            with patch('time.time', side_effect=[1000.0, 1000.1]):  # Mock time for response_time calculation
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.elapsed.total_seconds.return_value = 0.1
                mock_get.return_value = mock_response
                
                result = await router.test_endpoint_connectivity(endpoint.endpoint_id)
                
                # Based on actual implementation
                assert result["endpoint_id"] == endpoint.endpoint_id
                assert result["success"] is True
                assert abs(result["response_time"] - 0.1) < 0.001  # Allow tiny tolerance for floating point
                assert result["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_test_endpoint_connectivity_failure(self, registry, sample_endpoint_config):
        """Test endpoint connectivity testing - failure case."""
        router = RequestRouter(registry)
        endpoint = registry.register_endpoint(sample_endpoint_config)
        
        # Mock failed HTTP request
        with patch.object(router.proxy.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await router.test_endpoint_connectivity(endpoint.endpoint_id)
            
            assert result["endpoint_id"] == endpoint.endpoint_id
            assert result["success"] is False
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_test_endpoint_connectivity_not_found(self, registry):
        """Test endpoint connectivity testing for non-existent endpoint."""
        router = RequestRouter(registry)
        
        # Based on actual implementation, this raises ValueError
        with pytest.raises(ValueError, match="Endpoint not found"):
            await router.test_endpoint_connectivity("nonexistent")
    
    @pytest.mark.asyncio
    async def test_cleanup(self, registry):
        """Test router cleanup."""
        router = RequestRouter(registry)
        
        with patch.object(router.proxy, 'close', new_callable=AsyncMock) as mock_close:
            await router.cleanup()
            mock_close.assert_called_once() 