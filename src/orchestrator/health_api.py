"""
Health monitoring API endpoints.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from .health import HealthChecker
from .models import EndpointHealth
from .circuit_breaker import CircuitBreakerManager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


async def get_health_checker() -> HealthChecker:
    """Dependency to get the health checker instance."""
    # This will be injected by the main app
    from .app import get_health_checker
    return get_health_checker()


async def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Dependency to get the circuit breaker manager instance."""
    from .app import get_circuit_breaker_manager
    return get_circuit_breaker_manager()


@router.get("/status")
async def get_system_health_status(
    health_checker: HealthChecker = Depends(get_health_checker),
    cb_manager: CircuitBreakerManager = Depends(get_circuit_breaker_manager)
) -> Dict[str, Any]:
    """Get overall system health status including circuit breaker information."""
    try:
        summary = health_checker.get_health_summary()
        circuit_breaker_stats = cb_manager.get_all_circuit_breaker_stats()
        
        # Circuit breaker summary
        total_breakers = len(circuit_breaker_stats)
        open_breakers = sum(1 for stats in circuit_breaker_stats if stats["state"] == "open")
        half_open_breakers = sum(1 for stats in circuit_breaker_stats if stats["state"] == "half_open")
        closed_breakers = total_breakers - open_breakers - half_open_breakers
        
        # Determine overall system status
        health_percentage = summary["health_percentage"]
        circuit_breaker_health = (closed_breakers / total_breakers * 100) if total_breakers > 0 else 100
        
        # System is unhealthy if either health checks or circuit breakers indicate problems
        overall_health = min(health_percentage, circuit_breaker_health)
        
        if overall_health >= 90:
            system_status = "healthy"
        elif overall_health >= 70:
            system_status = "degraded"
        else:
            system_status = "unhealthy"
        
        return {
            "system_status": system_status,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "circuit_breaker_summary": {
                "total_circuit_breakers": total_breakers,
                "open_breakers": open_breakers,
                "half_open_breakers": half_open_breakers,
                "closed_breakers": closed_breakers,
                "health_percentage": circuit_breaker_health
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system health status: {str(e)}"
        )


@router.get("/endpoints")
async def get_all_endpoints_health(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> Dict[str, Any]:
    """Get health status of all monitored endpoints."""
    try:
        health_data = health_checker.get_all_health_status()
        
        # Convert to serializable format
        endpoints_health = []
        for health in health_data:
            endpoints_health.append({
                "endpoint_id": health.endpoint_id,
                "status": health.status.value,
                "last_check_time": health.last_check_time.isoformat(),
                "response_time": health.response_time,
                "error_message": health.error_message,
                "consecutive_failures": health.consecutive_failures,
                "consecutive_successes": health.consecutive_successes
            })
        
        # Sort by endpoint_id for consistent ordering
        endpoints_health.sort(key=lambda x: x["endpoint_id"])
        
        return {
            "endpoints": endpoints_health,
            "total_count": len(endpoints_health),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get endpoints health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get endpoints health: {str(e)}"
        )


@router.get("/endpoints/{endpoint_id}")
async def get_endpoint_health(
    endpoint_id: str,
    health_checker: HealthChecker = Depends(get_health_checker),
    cb_manager: CircuitBreakerManager = Depends(get_circuit_breaker_manager)
) -> Dict[str, Any]:
    """Get health status of a specific endpoint including circuit breaker information."""
    try:
        health = health_checker.get_endpoint_health(endpoint_id)
        
        if not health:
            raise HTTPException(
                status_code=404,
                detail=f"Health data not found for endpoint: {endpoint_id}"
            )
        
        # Get circuit breaker stats for this endpoint
        cb_stats = cb_manager.get_circuit_breaker_stats(endpoint_id)
        
        response = {
            "endpoint_id": health.endpoint_id,
            "status": health.status.value,
            "last_check_time": health.last_check_time.isoformat(),
            "response_time": health.response_time,
            "error_message": health.error_message,
            "consecutive_failures": health.consecutive_failures,
            "consecutive_successes": health.consecutive_successes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add circuit breaker information if available
        if cb_stats:
            response["circuit_breaker"] = {
                "state": cb_stats["state"],
                "failure_count": cb_stats["failure_count"],
                "last_failure_time": cb_stats["last_failure_time"],
                "last_success_time": cb_stats["last_success_time"],
                "state_changed_time": cb_stats["state_changed_time"],
                "half_open_calls": cb_stats["half_open_calls"]
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get endpoint health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get endpoint health: {str(e)}"
        )


@router.post("/check/{endpoint_id}")
async def trigger_immediate_health_check(
    endpoint_id: str,
    health_checker: HealthChecker = Depends(get_health_checker)
) -> Dict[str, Any]:
    """Trigger an immediate health check for a specific endpoint."""
    try:
        health = await health_checker.check_endpoint_immediately(endpoint_id)
        
        logger.info(f"Manual health check triggered for {endpoint_id}")
        
        return {
            "success": True,
            "message": f"Health check completed for {endpoint_id}",
            "result": {
                "endpoint_id": health.endpoint_id,
                "status": health.status.value,
                "last_check_time": health.last_check_time.isoformat(),
                "response_time": health.response_time,
                "error_message": health.error_message,
                "consecutive_failures": health.consecutive_failures,
                "consecutive_successes": health.consecutive_successes
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger health check: {str(e)}"
        )


@router.get("/unhealthy")
async def get_unhealthy_endpoints(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> Dict[str, Any]:
    """Get all endpoints that are currently unhealthy."""
    try:
        unhealthy = health_checker.get_unhealthy_endpoints()
        
        # Convert to serializable format
        unhealthy_endpoints = []
        for health in unhealthy:
            unhealthy_endpoints.append({
                "endpoint_id": health.endpoint_id,
                "status": health.status.value,
                "last_check_time": health.last_check_time.isoformat(),
                "response_time": health.response_time,
                "error_message": health.error_message,
                "consecutive_failures": health.consecutive_failures,
                "consecutive_successes": health.consecutive_successes
            })
        
        return {
            "unhealthy_endpoints": unhealthy_endpoints,
            "count": len(unhealthy_endpoints),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get unhealthy endpoints: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get unhealthy endpoints: {str(e)}"
        )


@router.get("/summary")
async def get_health_summary(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> Dict[str, Any]:
    """Get a summary of health monitoring status."""
    try:
        summary = health_checker.get_health_summary()
        
        return {
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health summary: {str(e)}"
        )


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    cb_manager: CircuitBreakerManager = Depends(get_circuit_breaker_manager)
) -> Dict[str, Any]:
    """Get circuit breaker status for all endpoints."""
    try:
        all_stats = cb_manager.get_all_circuit_breaker_stats()
        
        # Calculate summary statistics
        total_breakers = len(all_stats)
        open_breakers = sum(1 for stats in all_stats if stats["state"] == "open")
        half_open_breakers = sum(1 for stats in all_stats if stats["state"] == "half_open")
        closed_breakers = total_breakers - open_breakers - half_open_breakers
        
        return {
            "summary": {
                "total_circuit_breakers": total_breakers,
                "open_breakers": open_breakers,
                "half_open_breakers": half_open_breakers,
                "closed_breakers": closed_breakers,
                "health_percentage": (closed_breakers / total_breakers * 100) if total_breakers > 0 else 100
            },
            "circuit_breakers": all_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        )


@router.get("/circuit-breakers/open")
async def get_open_circuit_breakers(
    cb_manager: CircuitBreakerManager = Depends(get_circuit_breaker_manager)
) -> Dict[str, Any]:
    """Get all circuit breakers that are currently open."""
    try:
        all_stats = cb_manager.get_all_circuit_breaker_stats()
        open_breakers = [stats for stats in all_stats if stats["state"] == "open"]
        
        return {
            "open_circuit_breakers": open_breakers,
            "count": len(open_breakers),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get open circuit breakers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get open circuit breakers: {str(e)}"
        )