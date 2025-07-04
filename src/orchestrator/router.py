"""
Request router for dynamic endpoint routing and orchestration functionality.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import httpx
from fastapi import Request, Response, HTTPException
from fastapi.routing import APIRoute

from .registry import EndpointRegistry
from .models import RegisteredEndpoint, EndpointStatus, CircuitBreakerState
from .circuit_breaker import CircuitBreakerManager


logger = logging.getLogger(__name__)


class EndpointProxy:
    """Handles orchestrating requests to target endpoints."""
    
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True
        )
    
    async def forward_request(
        self,
        endpoint: RegisteredEndpoint,
        request: Request,
        path: str = ""
    ) -> tuple[int, Dict[str, str], bytes]:
        """Forward request to target endpoint."""
        target_url = str(endpoint.config.url)
        if path:
            # Remove leading slash to avoid double slashes
            path = path.lstrip('/')
            target_url = urljoin(target_url, path)
        
        # Prepare headers (exclude hop-by-hop headers)
        headers = self._filter_headers(dict(request.headers))
        
        # Get request body
        body = await request.body()
        
        try:
            logger.debug(f"Forwarding {request.method} request to {target_url}")
            
            response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )
            
            # Filter response headers
            response_headers = self._filter_response_headers(dict(response.headers))
            
            logger.debug(f"Received response: {response.status_code} from {target_url}")
            
            return response.status_code, response_headers, response.content
            
        except httpx.TimeoutException:
            logger.warning(f"Request timeout to {target_url}")
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except httpx.ConnectError:
            logger.error(f"Connection error to {target_url}")
            raise HTTPException(status_code=502, detail="Bad gateway - connection error")
        except Exception as e:
            logger.error(f"Orchestration error for {target_url}: {e}")
            raise HTTPException(status_code=502, detail=f"Orchestration error - {str(e)}")
    
    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter request headers before forwarding.
        
        Note: Authorization headers are intentionally passed through to backend services
        for authentication passthrough.
        """
        # Headers to exclude (hop-by-hop headers)
        exclude_headers = {
            'host', 'connection', 'proxy-connection', 'keep-alive',
            'proxy-authenticate', 'proxy-authorization', 'te', 'trailers',
            'transfer-encoding', 'upgrade'
        }
        
        return {
            key: value for key, value in headers.items()
            if key.lower() not in exclude_headers
        }
    
    def _filter_response_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter response headers before returning."""
        # Headers to exclude
        exclude_headers = {
            'connection', 'proxy-connection', 'keep-alive',
            'proxy-authenticate', 'proxy-authorization', 'te', 'trailers',
            'transfer-encoding', 'upgrade', 'server'
        }
        
        filtered = {
            key: value for key, value in headers.items()
            if key.lower() not in exclude_headers
        }
        
        # Add custom headers
        filtered['X-Orchestrated-By'] = 'Orchestrator-API'
        
        return filtered
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


class RequestRouter:
    """Manages dynamic route generation and request routing."""
    
    def __init__(self, registry: EndpointRegistry, circuit_breaker_manager: Optional[CircuitBreakerManager] = None) -> None:
        self.registry = registry
        self.circuit_breaker_manager = circuit_breaker_manager
        self.proxy = EndpointProxy()
        self.route_cache: Dict[str, RegisteredEndpoint] = {}
        self._update_cache()
    
    def _update_cache(self) -> None:
        """Update the route cache with current endpoints."""
        self.route_cache.clear()
        # Get all non-disabled endpoints (active, inactive, or unhealthy)
        all_endpoints = self.registry.list_endpoints(include_disabled=False)
        for endpoint in all_endpoints:
            # Create route pattern from endpoint name
            if endpoint.config.name:
                route_pattern = f"/{endpoint.config.name}"
                self.route_cache[route_pattern] = endpoint
                
                # Add version-specific route if version is specified
                if endpoint.config.version:
                    versioned_pattern = f"/{endpoint.config.version}/{endpoint.config.name}"
                    self.route_cache[versioned_pattern] = endpoint
    
    async def route_request(self, request: Request, path: str) -> Response:
        """Route incoming request to appropriate endpoint."""
        start_time = time.time()
        
        try:
            # Find matching endpoint
            endpoint = self._find_endpoint_for_path(path)
            if not endpoint:
                raise HTTPException(status_code=404, detail=f"No endpoint found for path: {path}")
            
            # Check if endpoint is disabled
            if endpoint.config.disabled:
                raise HTTPException(status_code=503, detail="Endpoint is disabled")
            
            # Check endpoint status
            if endpoint.status == EndpointStatus.UNHEALTHY:
                raise HTTPException(status_code=503, detail="Endpoint is unhealthy")
            
            # Check circuit breaker state
            if endpoint.circuit_breaker_state == CircuitBreakerState.OPEN:
                raise HTTPException(status_code=503, detail="Circuit breaker is open")
            
            # Check HTTP method
            if request.method not in [method.value for method in endpoint.config.methods]:
                allowed_methods = [method.value for method in endpoint.config.methods]
                raise HTTPException(
                    status_code=405,
                    detail=f"Method {request.method} not allowed. Allowed: {allowed_methods}"
                )
            
            # Extract relative path for forwarding
            relative_path = self._extract_relative_path(path, endpoint)
            
            # Forward request through circuit breaker if available
            if self.circuit_breaker_manager:
                async def make_request():
                    return await self.proxy.forward_request(endpoint, request, relative_path)
                
                result = await self.circuit_breaker_manager.execute_with_circuit_breaker(
                    endpoint.endpoint_id, make_request
                )
                
                # Handle circuit breaker fallback responses
                if isinstance(result, dict) and result.get("error") == "service_unavailable":
                    import json
                    # Circuit breaker returned a fallback response
                    fallback_response = Response(
                        content=json.dumps(result).encode(),
                        status_code=503,
                        headers={"Content-Type": "application/json"}
                    )
                    fallback_response.headers["X-Response-Time"] = f"{time.time() - start_time:.3f}s"
                    fallback_response.headers["X-Endpoint-ID"] = endpoint.endpoint_id
                    fallback_response.headers["X-Circuit-Breaker"] = "fallback"
                    return fallback_response
                
                status_code, headers, content = result
            else:
                # No circuit breaker - direct forwarding
                status_code, headers, content = await self.proxy.forward_request(
                    endpoint, request, relative_path
                )
            
            # Record success (circuit breaker handles this internally if used)
            if not self.circuit_breaker_manager:
                self.registry.record_success(endpoint.endpoint_id)
            
            # Create response
            response = Response(
                content=content,
                status_code=status_code,
                headers=headers
            )
            
            # Add timing header
            response_time = time.time() - start_time
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Endpoint-ID"] = endpoint.endpoint_id
            
            logger.info(f"Routed {request.method} {path} to {endpoint.endpoint_id} "
                       f"({status_code}) in {response_time:.3f}s")
            
            return response
            
        except HTTPException:
            # Record failure for routing errors (only if not using circuit breaker)
            if 'endpoint' in locals() and endpoint is not None and not self.circuit_breaker_manager:
                self.registry.record_failure(endpoint.endpoint_id)
            raise
        except Exception as e:
            # Record failure for any other errors (only if not using circuit breaker)
            if 'endpoint' in locals() and endpoint is not None and not self.circuit_breaker_manager:
                self.registry.record_failure(endpoint.endpoint_id)
            logger.error(f"Routing error for {path}: {e}")
            raise HTTPException(status_code=500, detail="Internal routing error")
    
    def _find_endpoint_for_path(self, path: str) -> Optional[RegisteredEndpoint]:
        """Find the best matching endpoint for a given path."""
        # Normalize path
        if not path.startswith('/'):
            path = f'/{path}'
        
        logger.debug(f"Looking for endpoint for path: {path}")
        logger.debug(f"Available routes: {list(self.route_cache.keys())}")
        
        # Try exact match first
        if path in self.route_cache:
            logger.debug(f"Found exact match for {path}")
            return self.route_cache[path]
        
        # Try to match by removing path segments
        path_parts = path.strip('/').split('/')
        
        # Try versioned routes (e.g., /v1/users)
        if len(path_parts) >= 2:
            version_candidate = f"/{path_parts[0]}/{path_parts[1]}"
            if version_candidate in self.route_cache:
                logger.debug(f"Found versioned match: {version_candidate}")
                return self.route_cache[version_candidate]
        
        # Try service name match (e.g., /users)
        if len(path_parts) >= 1:
            service_candidate = f"/{path_parts[0]}"
            if service_candidate in self.route_cache:
                logger.debug(f"Found service match: {service_candidate}")
                return self.route_cache[service_candidate]
        
        logger.debug(f"No endpoint found for path: {path}")
        return None
    
    def _extract_relative_path(self, full_path: str, endpoint: RegisteredEndpoint) -> str:
        """Extract the relative path to forward to the endpoint."""
        # Find the base path that was matched
        matched_pattern = None
        
        if endpoint.config.name:
            base_name = f"/{endpoint.config.name}"
            if full_path.startswith(base_name):
                matched_pattern = base_name
            
            if endpoint.config.version:
                versioned_base = f"/{endpoint.config.version}/{endpoint.config.name}"
                if full_path.startswith(versioned_base):
                    matched_pattern = versioned_base
        
        if matched_pattern:
            # Remove the matched pattern to get relative path
            relative_path = full_path[len(matched_pattern):]
            return relative_path.lstrip('/')
        
        return ""
    
    def refresh_routes(self) -> None:
        """Refresh route cache from registry."""
        self._update_cache()
        logger.info(f"Route cache refreshed with {len(self.route_cache)} routes")
    
    def get_active_routes(self) -> List[Dict[str, Any]]:
        """Get list of currently active routes."""
        routes = []
        for pattern, endpoint in self.route_cache.items():
            routes.append({
                "pattern": pattern,
                "endpoint_id": endpoint.endpoint_id,
                "target_url": str(endpoint.config.url),
                "methods": [method.value for method in endpoint.config.methods],
                "status": endpoint.status.value,
                "circuit_breaker_state": endpoint.circuit_breaker_state.value
            })
        return routes
    
    async def test_endpoint_connectivity(self, endpoint_id: str) -> Dict[str, Any]:
        """Test connectivity to a specific endpoint."""
        endpoint = self.registry.get_endpoint(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {endpoint_id}")
        
        test_url = str(endpoint.config.url)
        if endpoint.config.health_check_path:
            test_url = urljoin(test_url, endpoint.config.health_check_path)
        
        start_time = time.time()
        
        try:
            response = await self.proxy.client.get(test_url, timeout=10.0)
            response_time = time.time() - start_time
            
            return {
                "endpoint_id": endpoint_id,
                "url": test_url,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": 200 <= response.status_code < 400,
                "error": None
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint_id": endpoint_id,
                "url": test_url,
                "status_code": None,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.proxy.close()