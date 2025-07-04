"""
Configuration API endpoints for managing orchestrator configuration.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .config import ConfigManager
from .models import ConfigurationStatus, ErrorResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["configuration"])


class ReloadResponse(BaseModel):
    """Response for configuration reload."""
    success: bool
    message: str
    endpoints_count: int
    errors: list[str] = []


class ConfigStatusResponse(BaseModel):
    """Response for configuration status."""
    loaded: bool
    version: str
    config_path: str
    endpoints_count: int
    last_reload_error: str | None
    watching: bool


async def get_config_manager() -> ConfigManager:
    """Dependency to get the config manager instance."""
    # This will be injected by the main app
    from .app import get_config_manager
    return get_config_manager()


@router.post("/reload", response_model=ReloadResponse)
async def reload_configuration(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> ReloadResponse:
    """Manually trigger configuration reload."""
    try:
        logger.info("Manual configuration reload requested")
        
        config = await config_manager.reload_config()
        
        return ReloadResponse(
            success=True,
            message="Configuration reloaded successfully",
            endpoints_count=len(config.endpoints)
        )
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/status", response_model=ConfigStatusResponse)
async def get_configuration_status(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> ConfigStatusResponse:
    """Get current configuration status and metadata."""
    try:
        status = config_manager.get_status()
        
        return ConfigStatusResponse(
            loaded=status["loaded"],
            version=status["version"],
            config_path=status["config_path"],
            endpoints_count=status["endpoints_count"],
            last_reload_error=status.get("last_reload_error"),
            watching=status["watching"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get configuration status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration status: {str(e)}"
        )


@router.get("/endpoints")
async def list_configured_endpoints(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """List all configured endpoints."""
    try:
        config = config_manager.get_config()
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuration not loaded"
            )
        
        endpoints_data = []
        for endpoint in config.endpoints:
            endpoints_data.append({
                "url": str(endpoint.url),
                "name": endpoint.name,
                "version": endpoint.version,
                "methods": endpoint.methods,
                "auth_type": endpoint.auth_type,
                "disabled": endpoint.disabled,
                "health_check_path": endpoint.health_check_path,
                "timeout": endpoint.timeout
            })
        
        return {
            "endpoints": endpoints_data,
            "total_count": len(endpoints_data),
            "disabled_count": sum(1 for ep in config.endpoints if ep.disabled),
            "active_count": sum(1 for ep in config.endpoints if not ep.disabled)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list configured endpoints: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list configured endpoints: {str(e)}"
        )


@router.post("/validate")
async def validate_configuration_file(
    config_path: str,
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """Validate a configuration file without loading it."""
    try:
        is_valid, error_message = await config_manager.validate_config_file(config_path)
        
        return {
            "valid": is_valid,
            "error_message": error_message,
            "config_path": config_path
        }
        
    except Exception as e:
        logger.error(f"Failed to validate configuration file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate configuration file: {str(e)}"
        )