"""
Health check system for monitoring endpoint availability.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from urllib.parse import urljoin

from .registry import EndpointRegistry
from .models import (
    RegisteredEndpoint,
    EndpointHealth,
    EndpointStatus,
    HealthCheckConfig
)


logger = logging.getLogger(__name__)


class HealthChecker:
    """Manages health checks for registered endpoints."""
    
    def __init__(self, registry: EndpointRegistry, config: HealthCheckConfig) -> None:
        self.registry = registry
        self.config = config
        self.health_data: Dict[str, EndpointHealth] = {}
        self.running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout),
            follow_redirects=True
        )
    
    async def start(self) -> None:
        """Start the health check scheduler."""
        if not self.config.enabled or self.running:
            return
        
        self.running = True
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info(f"Health checker started with {self.config.interval}s interval")
    
    async def stop(self) -> None:
        """Stop the health check scheduler."""
        self.running = False
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
        
        await self.client.aclose()
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self) -> None:
        """Main health check loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all active endpoints."""
        endpoints = self.registry.list_endpoints(include_disabled=False)
        
        if not endpoints:
            return
        
        # Create tasks for concurrent health checks
        tasks = []
        for endpoint in endpoints:
            if not endpoint.config.disabled:
                task = asyncio.create_task(
                    self._check_endpoint_health(endpoint),
                    name=f"health_check_{endpoint.endpoint_id}"
                )
                tasks.append(task)
        
        if tasks:
            # Wait for all health checks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    endpoint_id = endpoints[i].endpoint_id
                    logger.error(f"Health check exception for {endpoint_id}: {result}")
    
    async def _check_endpoint_health(self, endpoint: RegisteredEndpoint) -> None:
        """Perform health check on a single endpoint."""
        endpoint_id = endpoint.endpoint_id
        check_url = self._get_health_check_url(endpoint)
        
        start_time = time.time()
        health_status = EndpointStatus.ACTIVE
        error_message = None
        
        try:
            response = await self.client.get(check_url)
            response_time = time.time() - start_time
            
            # Consider 2xx and 3xx as healthy
            is_healthy = 200 <= response.status_code < 400
            
            if not is_healthy:
                health_status = EndpointStatus.UNHEALTHY
                error_message = f"HTTP {response.status_code}"
            
            logger.debug(f"Health check for {endpoint_id}: {response.status_code} "
                        f"in {response_time:.3f}s")
            
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            health_status = EndpointStatus.UNHEALTHY
            error_message = "Request timeout"
            logger.warning(f"Health check timeout for {endpoint_id}")
            
        except httpx.ConnectError:
            response_time = time.time() - start_time
            health_status = EndpointStatus.UNHEALTHY
            error_message = "Connection error"
            logger.warning(f"Health check connection error for {endpoint_id}")
            
        except Exception as e:
            response_time = time.time() - start_time
            health_status = EndpointStatus.UNHEALTHY
            error_message = str(e)
            logger.error(f"Health check error for {endpoint_id}: {e}")
        
        # Update health data
        await self._update_health_status(
            endpoint_id, health_status, response_time, error_message
        )
    
    def _get_health_check_url(self, endpoint: RegisteredEndpoint) -> str:
        """Get the health check URL for an endpoint."""
        base_url = str(endpoint.config.url)
        
        if endpoint.config.health_check_path:
            return urljoin(base_url, endpoint.config.health_check_path)
        
        # Default health check - just ping the base URL
        return base_url
    
    async def _update_health_status(
        self,
        endpoint_id: str,
        status: EndpointStatus,
        response_time: float,
        error_message: Optional[str]
    ) -> None:
        """Update health status for an endpoint."""
        now = datetime.now()
        
        # Get or create health data
        if endpoint_id not in self.health_data:
            self.health_data[endpoint_id] = EndpointHealth(
                endpoint_id=endpoint_id,
                status=status,
                last_check_time=now,
                response_time=response_time,
                error_message=error_message
            )
        else:
            health = self.health_data[endpoint_id]
            health.last_check_time = now
            health.response_time = response_time
            health.error_message = error_message
            
            # Update consecutive counters
            if status == EndpointStatus.UNHEALTHY:
                health.consecutive_failures += 1
                health.consecutive_successes = 0
            else:
                health.consecutive_successes += 1
                health.consecutive_failures = 0
            
            # Determine overall health status based on thresholds
            if health.consecutive_failures >= self.config.unhealthy_threshold:
                health.status = EndpointStatus.UNHEALTHY
            elif health.consecutive_successes >= self.config.healthy_threshold:
                health.status = EndpointStatus.ACTIVE
        
        # Update registry with health status
        current_health = self.health_data[endpoint_id]
        self.registry.update_endpoint_status(endpoint_id, current_health.status)
        self.registry.update_health_check(endpoint_id, now)
        
        # Log status changes
        if endpoint_id in self.health_data:
            old_status = self.health_data[endpoint_id].status
            new_status = current_health.status
            if old_status != new_status:
                logger.info(f"Endpoint {endpoint_id} health changed: {old_status} -> {new_status}")
    
    async def check_endpoint_immediately(self, endpoint_id: str) -> EndpointHealth:
        """Perform immediate health check on a specific endpoint."""
        endpoint = self.registry.get_endpoint(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {endpoint_id}")
        
        await self._check_endpoint_health(endpoint)
        
        if endpoint_id not in self.health_data:
            raise RuntimeError(f"Health check failed to generate data for {endpoint_id}")
        
        return self.health_data[endpoint_id]
    
    def get_endpoint_health(self, endpoint_id: str) -> Optional[EndpointHealth]:
        """Get health status for a specific endpoint."""
        return self.health_data.get(endpoint_id)
    
    def get_all_health_status(self) -> List[EndpointHealth]:
        """Get health status for all monitored endpoints."""
        return list(self.health_data.values())
    
    def get_unhealthy_endpoints(self) -> List[EndpointHealth]:
        """Get all endpoints that are currently unhealthy."""
        return [
            health for health in self.health_data.values()
            if health.status == EndpointStatus.UNHEALTHY
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        total_endpoints = len(self.health_data)
        healthy_count = sum(
            1 for health in self.health_data.values()
            if health.status == EndpointStatus.ACTIVE
        )
        unhealthy_count = total_endpoints - healthy_count
        
        avg_response_time = 0.0
        if total_endpoints > 0:
            response_times = [
                health.response_time for health in self.health_data.values()
                if health.response_time is not None
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "total_endpoints": total_endpoints,
            "healthy_endpoints": healthy_count,
            "unhealthy_endpoints": unhealthy_count,
            "health_percentage": (healthy_count / total_endpoints * 100) if total_endpoints > 0 else 100,
            "average_response_time": avg_response_time,
            "last_check_time": max(
                (health.last_check_time for health in self.health_data.values()),
                default=None
            ),
            "config": {
                "enabled": self.config.enabled,
                "interval": self.config.interval,
                "timeout": self.config.timeout,
                "unhealthy_threshold": self.config.unhealthy_threshold,
                "healthy_threshold": self.config.healthy_threshold
            }
        }
    
    def cleanup_stale_health_data(self, max_age_hours: int = 24) -> None:
        """Remove health data for endpoints that no longer exist."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        active_endpoint_ids = {ep.endpoint_id for ep in self.registry.list_endpoints()}
        
        stale_ids = []
        for endpoint_id, health in self.health_data.items():
            if (endpoint_id not in active_endpoint_ids or 
                health.last_check_time < cutoff_time):
                stale_ids.append(endpoint_id)
        
        for endpoint_id in stale_ids:
            del self.health_data[endpoint_id]
            logger.debug(f"Removed stale health data for {endpoint_id}")
        
        if stale_ids:
            logger.info(f"Cleaned up {len(stale_ids)} stale health records")