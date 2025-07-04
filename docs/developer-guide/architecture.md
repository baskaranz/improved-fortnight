# Architecture Guide

**For Developers and Contributors**

This document explains the technical architecture of the Orchestrator API to help you understand how the system works and contribute effectively.

## 🏗️ High-Level Architecture

The Orchestrator API is a **FastAPI-based microservice gateway** that acts as a dynamic proxy between clients and backend services.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │────│  Orchestrator   │────│ Backend Service │
│                 │    │      API        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
               ┌─────────┐ ┌─────────┐ ┌─────────┐
               │Registry │ │ Health  │ │Circuit  │
               │         │ │Checker  │ │Breaker  │
               └─────────┘ └─────────┘ └─────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
               ┌─────────┐ ┌─────────┐ ┌─────────┐
               │Config   │ │Request  │ │ Auth    │
               │Manager  │ │Router   │ │Manager  │
               └─────────┘ └─────────┘ └─────────┘
```

### Key Design Principles

- **Asynchronous by Default** - All I/O operations use async/await
- **Configuration-Driven** - Behavior controlled via YAML configuration
- **Fault Tolerant** - Circuit breakers prevent cascading failures
- **Observable** - Comprehensive health monitoring and metrics
- **Modular** - Clear separation of concerns between components

## 📦 Core Components

### 1. FastAPI Application (`app.py`)

**Purpose**: Main application factory and lifecycle management

```python
# Key responsibilities:
# - Initialize all core components
# - Set up dependency injection
# - Configure middleware and exception handling
# - Manage application startup/shutdown

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize all components
    # Shutdown: Clean up resources
```

**Key Features**:
- **Lifespan Management**: Uses FastAPI's lifespan events for proper startup/shutdown
- **Dependency Injection**: Global component instances available via `Depends()`
- **Catch-All Route**: `/orchestrator/{path:path}` handles all routing
- **Middleware**: CORS, request ID, global exception handling

### 2. Configuration Manager (`config.py`)

**Purpose**: Load, validate, and hot-reload YAML configuration

```python
class ConfigManager:
    async def load_config(self) -> OrchestratorConfig
    async def reload_config(self) -> OrchestratorConfig
    def start_watching(self) -> None  # File system watching
```

**Key Features**:
- **Hot Reloading**: Automatically reloads on file changes using `watchdog`
- **Validation**: Uses Pydantic models for type safety
- **Callbacks**: Notifies other components of configuration changes
- **Default Generation**: Creates default config if none exists

### 3. Endpoint Registry (`registry.py`)

**Purpose**: In-memory store of all registered endpoints and their status

```python
class EndpointRegistry:
    def register_endpoint(self, config: EndpointConfig) -> RegisteredEndpoint
    def list_endpoints(self, status_filter=None) -> List[RegisteredEndpoint]
    def update_endpoint_status(self, endpoint_id: str, status: EndpointStatus)
```

**Key Features**:
- **Thread-Safe**: Uses RLock for concurrent access
- **Status Tracking**: Maintains real-time endpoint health status
- **Config Sync**: Automatically syncs with configuration changes
- **Query Interface**: Supports filtering and pagination

### 4. Request Router (`router.py`)

**Purpose**: Routes incoming requests to appropriate backend services

```python
class RequestRouter:
    async def route_request(self, request: Request, path: str) -> Response
    def _find_endpoint_for_path(self, path: str) -> Optional[RegisteredEndpoint]
    async def forward_request(self, endpoint, request, path) -> Response
```

**Request Flow**:
1. **Path Matching**: Find endpoint based on URL pattern
2. **Validation**: Check endpoint status, methods, circuit breaker
3. **Header Processing**: Filter and forward appropriate headers
4. **Proxying**: Forward request using HTTPX async client
5. **Response Processing**: Filter and return response

**Key Features**:
- **Dynamic Routing**: Route cache updated on registry changes
- **Authentication Passthrough**: Forwards auth headers to backends
- **Circuit Breaker Integration**: Respects circuit breaker states
- **Error Handling**: Proper HTTP status codes for various failures

### 5. Health Checker (`health.py`)

**Purpose**: Background monitoring of endpoint availability

```python
class HealthChecker:
    async def start(self) -> None  # Start background task
    async def _perform_health_checks(self) -> None  # Check all endpoints
    async def check_endpoint_immediately(self, endpoint_id: str) -> EndpointHealth
```

**Health Check Flow**:
1. **Periodic Execution**: Runs every N seconds (configurable)
2. **Concurrent Checks**: Checks all endpoints in parallel
3. **Threshold Logic**: Marks unhealthy after consecutive failures
4. **Status Updates**: Updates registry with health status

**Key Features**:
- **Configurable Intervals**: Balance between accuracy and performance
- **Custom Health Endpoints**: Support for custom health check paths
- **Failure Thresholds**: Avoid flapping with consecutive failure counting
- **Async Execution**: Non-blocking background operation

### 6. Circuit Breaker Manager (`circuit_breaker.py`)

**Purpose**: Implement circuit breaker pattern for fault tolerance

```python
class CircuitBreakerManager:
    async def execute_with_circuit_breaker(self, endpoint_id: str, func: Callable)
    async def reset_circuit_breaker(self, endpoint_id: str) -> bool
    def get_circuit_breaker_stats(self, endpoint_id: str) -> Dict
```

**Circuit Breaker States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Failures exceeded threshold, requests blocked
- **HALF_OPEN**: Testing if service recovered

**Key Features**:
- **Automatic State Management**: Transitions based on success/failure rates
- **Fallback Strategies**: Error responses, cached responses, defaults
- **Per-Endpoint Tracking**: Individual circuit breaker per service
- **Manual Control**: Admin APIs for manual reset/trip

## 🔄 Request Lifecycle

### 1. Incoming Request
```
Client Request → FastAPI → Request Router
```

### 2. Route Resolution
```python
# Router finds matching endpoint
endpoint = self._find_endpoint_for_path(path)

# Validation checks
if endpoint.status == EndpointStatus.UNHEALTHY:
    raise HTTPException(503, "Endpoint unhealthy")
if endpoint.circuit_breaker_state == CircuitBreakerState.OPEN:
    raise HTTPException(503, "Circuit breaker open")
```

### 3. Request Forwarding
```python
# Circuit breaker protection
async def make_request():
    return await self.proxy.forward_request(endpoint, request, path)

result = await circuit_breaker_manager.execute_with_circuit_breaker(
    endpoint.endpoint_id, make_request
)
```

### 4. Response Processing
```python
# Filter headers and create response
response = Response(
    content=content,
    status_code=status_code,
    headers=filtered_headers
)
response.headers["X-Orchestrated-By"] = "Orchestrator-API"
```

## 📊 Data Models (`models.py`)

### Configuration Models
```python
class OrchestratorConfig(BaseModel):
    endpoints: List[EndpointConfig]
    circuit_breaker: CircuitBreakerConfig
    health_check: HealthCheckConfig
    log_level: str

class EndpointConfig(BaseModel):
    url: HttpUrl
    name: Optional[str]
    methods: List[HTTPMethod]
    auth_type: AuthType
    timeout: int
```

### Runtime Models
```python
class RegisteredEndpoint(BaseModel):
    config: EndpointConfig
    status: EndpointStatus
    circuit_breaker_state: CircuitBreakerState
    consecutive_failures: int
    last_failure_time: Optional[datetime]

class EndpointHealth(BaseModel):
    endpoint_id: str
    status: EndpointStatus
    last_check_time: datetime
    response_time: Optional[float]
    error_message: Optional[str]
```

## 🔌 API Architecture

### Router Organization
```
/config      → config_api.py      → Configuration management
/registry    → registry_api.py    → Endpoint registration
/health      → health_api.py      → Health monitoring  
/router      → router_api.py      → Route management
/orchestrator → app.py (catch-all) → Request routing
```

### Dependency Injection
```python
# Global component instances
async def get_registry() -> EndpointRegistry:
    if _registry is None:
        raise RuntimeError("Registry not initialized")
    return _registry

# Usage in API endpoints
@router.get("/endpoints")
async def list_endpoints(
    registry: EndpointRegistry = Depends(get_registry)
):
    return registry.list_endpoints()
```

## 🔄 Background Tasks

### Health Monitoring Loop
```python
async def _health_check_loop(self) -> None:
    while self.running:
        try:
            await self._perform_health_checks()
            await asyncio.sleep(self.config.interval)
        except asyncio.CancelledError:
            break
```

### Configuration Watching
```python
class ConfigFileHandler(FileSystemEventHandler):
    def on_modified(self, event) -> None:
        if event.src_path == str(self.config_manager.config_path):
            asyncio.create_task(self.config_manager.reload_config())
```

## 🔐 Security Architecture

### Authentication Passthrough
- **No Auth Storage**: Orchestrator doesn't store authentication secrets
- **Header Forwarding**: Passes `Authorization` headers to backend services
- **Management API Security**: JWT-based auth for orchestrator management APIs

### Input Validation
- **Pydantic Models**: All inputs validated with type checking
- **URL Validation**: HTTP URLs validated before registration
- **Header Filtering**: Removes hop-by-hop headers

## 📈 Performance Considerations

### Async Architecture
- **Non-blocking I/O**: All network operations use async/await
- **Connection Pooling**: HTTPX client reuses HTTP connections
- **Concurrent Health Checks**: Parallel execution for better performance

### Memory Management
- **Bounded Collections**: Circuit breaker stats and health data have size limits
- **Cleanup Tasks**: Periodic cleanup of stale data
- **Efficient Routing**: Route cache for fast path matching

## 🧪 Testing Architecture

### Test Organization
```
tests/
├── unit/           # Component isolation tests
├── integration/    # Component interaction tests
├── e2e/           # Full request flow tests
└── utils/         # Test utilities and fixtures
```

### Mock Services
- **FastAPI Test Services**: Create mock backends for testing
- **Configurable Responses**: Test various success/failure scenarios
- **Authentication Testing**: Test auth passthrough behavior

## 🔍 Debugging & Observability

### Logging
- **Structured Logging**: JSON-formatted logs with request IDs
- **Component-Specific Loggers**: Separate loggers per component
- **Configurable Levels**: Debug, info, warning, error levels

### Metrics
- **Request Tracking**: Count, timing, status codes
- **Health Metrics**: Endpoint availability percentages
- **Circuit Breaker Events**: State changes and trip counts

### Request Tracing
- **Request IDs**: Unique ID per request for tracing
- **Header Propagation**: Request ID passed to backend services
- **Response Time Tracking**: End-to-end timing information

## 🔄 Extension Points

### Adding New Features

1. **New Health Check Types**:
   - Extend `HealthChecker` class
   - Add configuration options
   - Update health API endpoints

2. **New Circuit Breaker Strategies**:
   - Implement new `FallbackStrategy` types
   - Add configuration validation
   - Update circuit breaker manager

3. **New API Endpoints**:
   - Create new router file (`feature_api.py`)
   - Add to main app router inclusion
   - Add corresponding tests

### Configuration Extensions
- **New Endpoint Properties**: Add to `EndpointConfig` model
- **New Global Settings**: Add to `OrchestratorConfig` model
- **Custom Validation**: Add Pydantic validators

This architecture provides a solid foundation for building a scalable, fault-tolerant API gateway while maintaining clean separation of concerns and extensive testing capabilities. 