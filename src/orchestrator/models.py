"""
Data models for the orchestrator service using Pydantic.
"""

import time
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re


class HTTPMethod(str, Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT" 
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(str, Enum):
    """Authentication types (for documentation purposes only)."""
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class EndpointStatus(str, Enum):
    """Endpoint status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    UNHEALTHY = "unhealthy"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FallbackStrategy(str, Enum):
    """Fallback strategies for circuit breaker."""
    ERROR_RESPONSE = "error_response"
    CACHED_RESPONSE = "cached_response"
    DEFAULT_RESPONSE = "default_response"
    REDIRECT = "redirect"


class EndpointConfig(BaseModel):
    """Configuration for a single endpoint."""
    url: HttpUrl = Field(..., description="The URL of the attached endpoint")
    name: Optional[str] = Field(None, description="Unique identifier for the endpoint")
    version: Optional[str] = Field(None, description="API version of the endpoint")
    methods: List[HTTPMethod] = Field(default=[HTTPMethod.GET], description="Supported HTTP methods")
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication type expected by backend (documentation only)")
    disabled: bool = Field(default=False, description="Whether the endpoint is disabled")
    health_check_path: Optional[str] = Field(None, description="Custom health check path")
    timeout: int = Field(default=30, description="Request timeout in seconds", ge=1, le=300)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^v?\d+(\.\d+)*$', v):
            raise ValueError('Version must be in format like "1.0.0" or "v1.0.0"')
        return v


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""
    failure_threshold: int = Field(default=5, description="Number of failures to trip circuit", ge=1)
    reset_timeout: int = Field(default=60, description="Time before attempting reset (seconds)", ge=1)
    half_open_max_calls: int = Field(default=3, description="Max calls in half-open state", ge=1)
    fallback_strategy: FallbackStrategy = Field(default=FallbackStrategy.ERROR_RESPONSE)
    fallback_response: Optional[Dict[str, Any]] = Field(None, description="Custom fallback response")


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    enabled: bool = Field(default=True, description="Whether health checks are enabled")
    interval: int = Field(default=30, description="Health check interval in seconds", ge=5)
    timeout: int = Field(default=10, description="Health check timeout in seconds", ge=1)
    unhealthy_threshold: int = Field(default=3, description="Failures to mark unhealthy", ge=1)
    healthy_threshold: int = Field(default=2, description="Successes to mark healthy", ge=1)


class OrchestratorConfig(BaseModel):
    """Main orchestrator configuration."""
    endpoints: List[EndpointConfig] = Field(default=[], description="List of endpoints")
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    log_level: str = Field(default="INFO", description="Logging level")


class RegisteredEndpoint(BaseModel):
    """Runtime endpoint information."""
    config: EndpointConfig
    registration_time: float = Field(default_factory=time.time, description="Registration timestamp (epoch)")
    last_health_check: Optional[float] = Field(None, description="Last health check timestamp (epoch)")
    status: EndpointStatus = Field(default=EndpointStatus.ACTIVE)
    circuit_breaker_state: CircuitBreakerState = Field(default=CircuitBreakerState.CLOSED)
    consecutive_failures: int = Field(default=0)
    last_failure_time: Optional[float] = Field(None, description="Last failure timestamp (epoch)")
    
    @property
    def endpoint_id(self) -> str:
        """Generate unique endpoint ID."""
        if self.config.name:
            return self.config.name
        return f"endpoint_{hash(str(self.config.url))}"
    
    @property
    def registration_time_iso(self) -> str:
        """Get registration time in ISO format."""
        return datetime.fromtimestamp(self.registration_time).isoformat() + 'Z'
    
    @property
    def last_health_check_iso(self) -> Optional[str]:
        """Get last health check time in ISO format."""
        if self.last_health_check:
            return datetime.fromtimestamp(self.last_health_check).isoformat() + 'Z'
        return None
    
    @property
    def last_failure_time_iso(self) -> Optional[str]:
        """Get last failure time in ISO format."""
        if self.last_failure_time:
            return datetime.fromtimestamp(self.last_failure_time).isoformat() + 'Z'
        return None
    
    def __hash__(self) -> int:
        return hash(str(self.config.url))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegisteredEndpoint):
            return False
        return str(self.config.url) == str(other.config.url)


class EndpointHealth(BaseModel):
    """Health status of an endpoint."""
    endpoint_id: str
    status: EndpointStatus
    last_check_time: float = Field(..., description="Last check timestamp (epoch)")
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def last_check_time_iso(self) -> str:
        """Get last check time in ISO format."""
        return datetime.fromtimestamp(self.last_check_time).isoformat() + 'Z'


class ConfigurationStatus(BaseModel):
    """Configuration status information."""
    loaded: bool = False
    last_reload: Optional[float] = Field(None, description="Last reload timestamp (epoch)")
    version: str = "unknown"
    error_message: Optional[str] = None
    endpoints_count: int = 0
    
    @property
    def last_reload_iso(self) -> Optional[str]:
        """Get last reload time in ISO format."""
        if self.last_reload:
            return datetime.fromtimestamp(self.last_reload).isoformat() + 'Z'
        return None
    
    
class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = Field(None, description="Error timestamp (epoch)")
    timestamp_iso: Optional[str] = Field(None, description="Error timestamp (ISO format)")
    request_id: Optional[str] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        if 'timestamp_iso' not in data and 'timestamp' in data:
            data['timestamp_iso'] = datetime.fromtimestamp(data['timestamp']).isoformat() + 'Z'
        super().__init__(**data)