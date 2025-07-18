"""
Router API endpoints for managing request routing.
"""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Response

from .router import RequestRouter
from .registry import EndpointRegistry


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/router", tags=["routing"])


async def get_router() -> RequestRouter:
    """Dependency to get the request router instance."""
    # This will be injected by the main app
    from .app import get_router
    return get_router()


@router.get("/routes")
async def list_active_routes(
    request_router: RequestRouter = Depends(get_router)
) -> Dict[str, Any]:
    """List all currently active routes."""
    try:
        routes = request_router.get_active_routes()
        
        return {
            "routes": routes,
            "total_count": len(routes),
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to list active routes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list active routes: {str(e)}"
        )


@router.get("/test/{endpoint_id}")
async def test_endpoint_connectivity(
    endpoint_id: str,
    request_router: RequestRouter = Depends(get_router)
) -> Dict[str, Any]:
    """Test connectivity to a specific endpoint."""
    try:
        result = await request_router.test_endpoint_connectivity(endpoint_id)
        
        return {
            "test_result": result,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to test endpoint connectivity: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test endpoint connectivity: {str(e)}"
        )


@router.post("/refresh")
async def refresh_route_mappings(
    request_router: RequestRouter = Depends(get_router)
) -> Dict[str, Any]:
    """Refresh route mappings from the registry."""
    try:
        request_router.refresh_routes()
        routes = request_router.get_active_routes()
        
        logger.info("Route mappings refreshed manually")
        
        return {
            "success": True,
            "message": "Route mappings refreshed successfully",
            "active_routes_count": len(routes),
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh route mappings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh route mappings: {str(e)}"
        )


@router.get("/debug/{path:path}")
async def debug_route_resolution(
    path: str,
    request_router: RequestRouter = Depends(get_router)
) -> Dict[str, Any]:
    """Debug route resolution for a given path."""
    try:
        # This is a debug endpoint to help understand routing
        normalized_path = f"/{path}" if not path.startswith('/') else path
        
        # Try to find endpoint (using internal method for debugging)
        endpoint = request_router._find_endpoint_for_path(normalized_path)
        
        if endpoint:
            relative_path = request_router._extract_relative_path(normalized_path, endpoint)
            
            return {
                "input_path": path,
                "normalized_path": normalized_path,
                "matched_endpoint": {
                    "endpoint_id": endpoint.endpoint_id,
                    "name": endpoint.config.name,
                    "url": str(endpoint.config.url),
                    "methods": [method.value for method in endpoint.config.methods],
                    "status": endpoint.status.value
                },
                "relative_path": relative_path,
                "would_forward_to": str(endpoint.config.url) + "/" + relative_path if relative_path else str(endpoint.config.url)
            }
        else:
            return {
                "input_path": path,
                "normalized_path": normalized_path,
                "matched_endpoint": None,
                "error": "No matching endpoint found"
            }
        
    except Exception as e:
        logger.error(f"Failed to debug route resolution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to debug route resolution: {str(e)}"
        )