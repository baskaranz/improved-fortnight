"""
Registry API endpoints for managing endpoint registration.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from .registry import EndpointRegistry
from .models import EndpointConfig, EndpointStatus, RegisteredEndpoint


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["registry"])


class EndpointRegistrationRequest(BaseModel):
    """Request model for manual endpoint registration."""
    config: EndpointConfig


class EndpointRegistrationResponse(BaseModel):
    """Response for endpoint registration."""
    success: bool
    message: str
    endpoint_id: str
    endpoint_url: str


class EndpointDetailsResponse(BaseModel):
    """Detailed endpoint information."""
    endpoint_id: str
    url: str
    name: Optional[str]
    version: Optional[str]
    methods: List[str]
    auth_type: str
    disabled: bool
    status: str
    circuit_breaker_state: str
    registration_time: datetime
    last_health_check: Optional[datetime]
    consecutive_failures: int
    last_failure_time: Optional[datetime]
    timeout: int


class EndpointListResponse(BaseModel):
    """Response for endpoint listing."""
    endpoints: List[EndpointDetailsResponse]
    total_count: int
    active_count: int
    unhealthy_count: int
    disabled_count: int


async def get_registry() -> EndpointRegistry:
    """Dependency to get the endpoint registry instance."""
    # This will be injected by the main app
    from .app import get_registry
    return get_registry()


def _endpoint_to_response(endpoint: RegisteredEndpoint) -> EndpointDetailsResponse:
    """Convert RegisteredEndpoint to response model."""
    return EndpointDetailsResponse(
        endpoint_id=endpoint.endpoint_id,
        url=str(endpoint.config.url),
        name=endpoint.config.name,
        version=endpoint.config.version,
        methods=[method.value for method in endpoint.config.methods],
        auth_type=endpoint.config.auth_type.value,
        disabled=endpoint.config.disabled,
        status=endpoint.status.value,
        circuit_breaker_state=endpoint.circuit_breaker_state.value,
        registration_time=endpoint.registration_time,
        last_health_check=endpoint.last_health_check,
        consecutive_failures=endpoint.consecutive_failures,
        last_failure_time=endpoint.last_failure_time,
        timeout=endpoint.config.timeout
    )


@router.get("/endpoints", response_model=EndpointListResponse)
async def list_endpoints(
    status: Optional[EndpointStatus] = Query(None, description="Filter by status"),
    include_disabled: bool = Query(True, description="Include disabled endpoints"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of endpoints to return"),
    offset: int = Query(0, ge=0, description="Number of endpoints to skip"),
    registry: EndpointRegistry = Depends(get_registry)
) -> EndpointListResponse:
    """List all registered endpoints with optional filtering and pagination."""
    try:
        # Get all endpoints with filtering
        endpoints = registry.list_endpoints(
            status_filter=status,
            include_disabled=include_disabled
        )
        
        # Apply pagination
        total_count = len(endpoints)
        paginated_endpoints = endpoints[offset:offset + limit]
        
        # Convert to response format
        endpoint_responses = [_endpoint_to_response(ep) for ep in paginated_endpoints]
        
        # Calculate counts
        stats = registry.get_registry_stats()
        
        return EndpointListResponse(
            endpoints=endpoint_responses,
            total_count=total_count,
            active_count=stats["active"],
            unhealthy_count=stats["unhealthy"],
            disabled_count=stats["disabled"]
        )
        
    except Exception as e:
        logger.error(f"Failed to list endpoints: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list endpoints: {str(e)}"
        )


@router.get("/endpoints/{endpoint_id}", response_model=EndpointDetailsResponse)
async def get_endpoint_details(
    endpoint_id: str,
    registry: EndpointRegistry = Depends(get_registry)
) -> EndpointDetailsResponse:
    """Get detailed information about a specific endpoint."""
    try:
        endpoint = registry.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise HTTPException(
                status_code=404,
                detail=f"Endpoint not found: {endpoint_id}"
            )
        
        return _endpoint_to_response(endpoint)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get endpoint details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get endpoint details: {str(e)}"
        )


@router.post("/endpoints", response_model=EndpointRegistrationResponse)
async def register_endpoint(
    request: EndpointRegistrationRequest,
    registry: EndpointRegistry = Depends(get_registry)
) -> EndpointRegistrationResponse:
    """Manually register a new endpoint."""
    try:
        endpoint = registry.register_endpoint(request.config)
        
        logger.info(f"Manually registered endpoint: {endpoint.endpoint_id}")
        
        return EndpointRegistrationResponse(
            success=True,
            message="Endpoint registered successfully",
            endpoint_id=endpoint.endpoint_id,
            endpoint_url=str(endpoint.config.url)
        )
        
    except ValueError as e:
        logger.warning(f"Invalid endpoint registration request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to register endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register endpoint: {str(e)}"
        )


@router.delete("/endpoints/{endpoint_id}")
async def unregister_endpoint(
    endpoint_id: str,
    registry: EndpointRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """Unregister an endpoint."""
    try:
        success = registry.unregister_endpoint(endpoint_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Endpoint not found: {endpoint_id}"
            )
        
        logger.info(f"Manually unregistered endpoint: {endpoint_id}")
        
        return {
            "success": True,
            "message": f"Endpoint {endpoint_id} unregistered successfully",
            "endpoint_id": endpoint_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unregister endpoint: {str(e)}"
        )


@router.put("/endpoints/{endpoint_id}/status")
async def update_endpoint_status(
    endpoint_id: str,
    status: EndpointStatus,
    registry: EndpointRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """Update the status of an endpoint."""
    try:
        success = registry.update_endpoint_status(endpoint_id, status)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Endpoint not found: {endpoint_id}"
            )
        
        logger.info(f"Updated endpoint {endpoint_id} status to {status.value}")
        
        return {
            "success": True,
            "message": f"Endpoint status updated to {status.value}",
            "endpoint_id": endpoint_id,
            "new_status": status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update endpoint status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update endpoint status: {str(e)}"
        )


@router.get("/stats")
async def get_registry_stats(
    registry: EndpointRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """Get registry statistics."""
    try:
        stats = registry.get_registry_stats()
        
        current_time = time.time()
        return {
            "registry_stats": stats,
            "timestamp": current_time,
            "timestamp_iso": datetime.fromtimestamp(current_time).isoformat() + 'Z'
        }
        
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get registry stats: {str(e)}"
        )


@router.post("/sync")
async def sync_registry_with_config(
    registry: EndpointRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """Synchronize registry with current configuration."""
    try:
        # Get current config
        from .app import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuration not loaded"
            )
        
        result = registry.sync_with_config(config)
        
        logger.info("Manual registry synchronization completed")
        
        return {
            "success": True,
            "message": "Registry synchronized with configuration",
            "sync_result": result,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync registry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync registry: {str(e)}"
        )