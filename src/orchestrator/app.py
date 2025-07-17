"""
FastAPI application factory and main application setup.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import ConfigManager
from .registry import EndpointRegistry
from .router import RequestRouter
from .health import HealthChecker
from .circuit_breaker import CircuitBreakerManager

from .config_api import router as config_router
from .registry_api import router as registry_router
from .router_api import router as router_router
from .health_api import router as health_router

from .models import ErrorResponse


# Global instances
_config_manager: ConfigManager | None = None
_registry: EndpointRegistry | None = None
_request_router: RequestRouter | None = None
_health_checker: HealthChecker | None = None
_circuit_breaker_manager: CircuitBreakerManager | None = None


logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _config_manager, _registry, _request_router, _health_checker, _circuit_breaker_manager
    
    # Startup
    logger.info("Starting orchestrator service...")
    
    try:
        # Initialize configuration manager
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
        _config_manager = ConfigManager(config_path)
        
        # Load initial configuration
        config = await _config_manager.load_config()
        logger.info(f"Loaded configuration with {len(config.endpoints)} endpoints")
        
        # Initialize registry
        _registry = EndpointRegistry()
        
        # Initialize circuit breaker manager
        _circuit_breaker_manager = CircuitBreakerManager(_registry, config.circuit_breaker)
        
        # Initialize request router
        _request_router = RequestRouter(_registry, _circuit_breaker_manager)
        
        # Initialize health checker
        _health_checker = HealthChecker(_registry, config.health_check)
        
        # Register endpoints from configuration
        if config.endpoints:
            _registry.bulk_register(config.endpoints)
            logger.info(f"Registered {len(config.endpoints)} endpoints")
        
        # Set up config reload callback
        def on_config_reload(new_config):
            """Callback for configuration reloads."""
            logger.info("Configuration reloaded, syncing registry...")
            result = _registry.sync_with_config(new_config)
            if _request_router:
                _request_router.refresh_routes()
            logger.info(f"Registry sync result: {result}")
        
        _config_manager.add_reload_callback(on_config_reload)
        
        # Start watching configuration file
        _config_manager.start_watching()
        
        # Start health checker
        await _health_checker.start()
        
        logger.info("Orchestrator service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start orchestrator service: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down orchestrator service...")
    
    if _health_checker:
        await _health_checker.stop()
    
    if _request_router:
        await _request_router.cleanup()
    
    if _config_manager:
        _config_manager.stop_watching()
    
    logger.info("Orchestrator service shutdown complete")


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    if _config_manager is None:
        raise RuntimeError("Config manager not initialized")
    return _config_manager


def get_registry() -> EndpointRegistry:
    """Get the global registry instance."""
    if _registry is None:
        raise RuntimeError("Registry not initialized")
    return _registry


def get_router() -> RequestRouter:
    """Get the global request router instance."""
    if _request_router is None:
        raise RuntimeError("Request router not initialized")
    return _request_router


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    if _health_checker is None:
        raise RuntimeError("Health checker not initialized")
    return _health_checker


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager instance."""
    if _circuit_breaker_manager is None:
        raise RuntimeError("Circuit breaker manager not initialized")
    return _circuit_breaker_manager


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error="internal_server_error",
        message="An internal server error occurred",
        details={"path": str(request.url), "method": request.method}
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


async def add_request_id_header(request: Request, call_next) -> Response:
    """Add request ID to response headers."""
    import uuid
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state for logging
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    # Create FastAPI app with lifespan manager
    app = FastAPI(
        title="Orchestrator API",
        description="A scalable and extensible API gateway that dynamically routes requests to attached API endpoints",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request ID middleware
    app.middleware("http")(add_request_id_header)
    
    # Add global exception handler
    app.add_exception_handler(Exception, global_exception_handler)
    
    # Include routers
    app.include_router(config_router)
    app.include_router(registry_router)
    app.include_router(router_router)
    app.include_router(health_router)
    
    # Dynamic routing endpoint - catch-all for orchestrating requests with authentication passthrough
    @app.api_route("/orchestrator/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def orchestrator_request(request: Request, path: str):
        """Orchestrate requests to registered endpoints with authentication passthrough."""
        try:
            request_router = get_router()
            return await request_router.route_request(request, path)
        except Exception as e:
            logger.error(f"Orchestrator routing error: {e}")
            raise
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        try:
            config_manager = get_config_manager()
            registry = get_registry()
            health_checker = get_health_checker()
            
            config_status = config_manager.get_status()
            registry_stats = registry.get_registry_stats()
            health_summary = health_checker.get_health_summary()
            
            return {
                "status": "healthy",
                "timestamp": datetime.fromtimestamp(time.time()).isoformat() + 'Z',
                "configuration": {
                    "loaded": config_status["loaded"],
                    "endpoints_count": config_status["endpoints_count"]
                },
                "registry": {
                    "total_endpoints": registry_stats["total"],
                    "active_endpoints": registry_stats["active"],
                    "unhealthy_endpoints": registry_stats["unhealthy"]
                },
                "health_monitoring": {
                    "enabled": health_summary["config"]["enabled"],
                    "monitored_endpoints": health_summary["total_endpoints"],
                    "healthy_endpoints": health_summary["healthy_endpoints"],
                    "health_percentage": health_summary["health_percentage"]
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic service information."""
        return {
            "service": "Orchestrator API",
            "version": "0.1.0",
            "description": "FastAPI Orchestrating Service with Authentication Passthrough",
            "endpoints": {
                "health": "/health",
                "configuration": "/config",
                "registry": "/registry",
                "routing": "/router",
                "health_monitoring": "/health",
                "orchestrator": "/orchestrator/{path}",
                "docs": "/docs"
            }
        }
    
    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
) -> None:
    """Run the FastAPI server."""
    uvicorn.run(
        "src.orchestrator.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )


if __name__ == "__main__":
    run_server()