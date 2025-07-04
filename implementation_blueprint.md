# Python FastAPI Orchestrating Service - Implementation Blueprint

## High-Level Architecture Overview

The service consists of these core components:
1. **Configuration Manager** - YAML parsing and dynamic reloading
2. **Endpoint Registry** - Dynamic endpoint management
3. **Request Router** - Intelligent request routing
4. **Circuit Breaker** - Fault tolerance and health monitoring
5. **Authentication Middleware** - JWT-based security
6. **Statistics API** - Monitoring and metrics
7. **Error Handling & Logging** - Comprehensive error management

## Phase 1: Foundation and Core Infrastructure

### Step 1.1: Project Setup and Basic FastAPI Structure
- Initialize Python project with proper structure
- Set up FastAPI application with basic configuration
- Implement dependency management and virtual environment
- Create basic project structure with separation of concerns

### Step 1.2: Configuration Management Foundation
- Implement YAML configuration parsing
- Create configuration models using Pydantic
- Add configuration validation and error handling
- Implement basic configuration reloading mechanism

### Step 1.3: Basic Endpoint Registry
- Create endpoint model and registry structure
- Implement endpoint registration and unregistration
- Add basic endpoint storage and retrieval
- Create foundation for dynamic endpoint management

## Phase 2: Core Routing and Health Management

### Step 2.1: Request Router Foundation
- Implement basic request routing logic
- Create dynamic route generation based on configuration
- Add HTTP method validation and forwarding
- Implement basic request/response handling

### Step 2.2: Health Check System
- Create health check mechanism for endpoints
- Implement endpoint status monitoring
- Add periodic health check scheduling
- Create health status reporting

### Step 2.3: Circuit Breaker Implementation
- Implement circuit breaker pattern
- Add failure tracking and state management
- Create circuit breaker configuration
- Integrate with health check system

## Phase 3: Security and Monitoring

### Step 3.1: Authentication Middleware
- Implement JWT authentication middleware
- Add token validation and extraction
- Create authentication decorators and dependencies
- Implement security for orchestrator endpoints

### Step 3.2: Statistics and Monitoring API
- Create endpoint statistics collection
- Implement statistics API endpoints
- Add metrics for request counts, latency, errors
- Create comprehensive endpoint status reporting

### Step 3.3: Error Handling and Logging
- Implement comprehensive error handling
- Add structured logging throughout the system
- Create error response standardization
- Add debugging and monitoring capabilities

## Phase 4: Testing and Deployment

### Step 4.1: Testing Infrastructure
- Set up pytest testing framework
- Create unit tests for core components
- Implement integration tests
- Add end-to-end testing scenarios

### Step 4.2: Dockerization and Deployment
- Create Docker configuration
- Implement health check endpoints for containers
- Add deployment scripts and configuration
- Create monitoring and alerting setup

---

## Detailed Implementation Steps

### Phase 1 Breakdown

#### Step 1.1: Project Setup and Basic FastAPI Structure

**Iteration 1.1.1: Basic Project Structure**
- Create directory structure
- Set up pyproject.toml/requirements.txt
- Initialize basic FastAPI app
- Create main entry point

**Iteration 1.1.2: Core Application Framework**
- Implement application factory pattern
- Add basic configuration loading
- Create modular structure for components
- Set up basic error handling

**Iteration 1.1.3: Development Environment**
- Add development dependencies
- Create basic testing setup
- Add code formatting and linting
- Create development scripts

#### Step 1.2: Configuration Management Foundation

**Iteration 1.2.1: Configuration Models**
- Create Pydantic models for configuration
- Implement endpoint configuration schema
- Add validation for required fields
- Create type-safe configuration handling

**Iteration 1.2.2: YAML Parser Implementation**
- Implement YAML file parsing
- Add configuration file validation
- Create error handling for malformed YAML
- Add configuration loading mechanism

**Iteration 1.2.3: Dynamic Configuration Reloading**
- Implement file watching for configuration changes
- Create configuration reload API endpoint
- Add configuration version tracking
- Implement graceful configuration updates

#### Step 1.3: Basic Endpoint Registry

**Iteration 1.3.1: Endpoint Models and Storage**
- Create endpoint data models
- Implement in-memory endpoint registry
- Add endpoint registration logic
- Create endpoint retrieval methods

**Iteration 1.3.2: Dynamic Registration Logic**
- Implement endpoint registration from configuration
- Add endpoint unregistration capability
- Create endpoint status tracking
- Add validation for endpoint conflicts

**Iteration 1.3.3: Registry Management API**
- Create endpoints for manual registration
- Add registry inspection capabilities
- Implement endpoint filtering and search
- Add registry state management

### Phase 2 Breakdown

#### Step 2.1: Request Router Foundation

**Iteration 2.1.1: Basic Routing Logic**
- Implement request matching to endpoints
- Create HTTP method validation
- Add basic request forwarding
- Implement response handling

**Iteration 2.1.2: Dynamic Route Generation**
- Create FastAPI route generation from registry
- Implement path parameter handling
- Add query parameter forwarding
- Create header propagation logic

**Iteration 2.1.3: Advanced Routing Features**
- Add request transformation capabilities
- Implement response caching mechanisms
- Create routing priorities and fallbacks
- Add load balancing for multiple endpoints

#### Step 2.2: Health Check System

**Iteration 2.2.1: Basic Health Checks**
- Implement endpoint health check logic
- Create health status models
- Add periodic health check scheduling
- Implement health status storage

**Iteration 2.2.2: Health Check Configuration**
- Add configurable health check intervals
- Implement custom health check endpoints
- Create health check timeout handling
- Add health check retry logic

**Iteration 2.2.3: Health Monitoring Integration**
- Integrate health checks with endpoint registry
- Create health status API endpoints
- Add health check event logging
- Implement health change notifications

#### Step 2.3: Circuit Breaker Implementation

**Iteration 2.3.1: Circuit Breaker Core Logic**
- Implement circuit breaker state machine
- Create failure threshold tracking
- Add circuit breaker state persistence
- Implement state transition logic

**Iteration 2.3.2: Circuit Breaker Configuration**
- Add configurable circuit breaker parameters
- Implement different failure strategies
- Create circuit breaker reset mechanisms
- Add manual circuit breaker controls

**Iteration 2.3.3: Integration with Request Router**
- Integrate circuit breaker with routing logic
- Add fallback response handling
- Create circuit breaker metrics
- Implement circuit breaker API endpoints

### Phase 3 Breakdown

#### Step 3.1: Authentication Middleware

**Iteration 3.1.1: JWT Token Handling**
- Implement JWT token validation
- Create token parsing and verification
- Add token expiration handling
- Implement token refresh mechanisms

**Iteration 3.1.2: Authentication Middleware**
- Create FastAPI authentication dependencies
- Implement route protection decorators
- Add user context extraction
- Create authentication error handling

**Iteration 3.1.3: Authorization Integration**
- Add role-based access control
- Implement endpoint-specific permissions
- Create authorization policies
- Add security logging and auditing

#### Step 3.2: Statistics and Monitoring API

**Iteration 3.2.1: Basic Statistics Collection**
- Implement request/response metrics collection
- Create endpoint performance tracking
- Add error rate monitoring
- Implement basic statistics storage

**Iteration 3.2.2: Statistics API Endpoints**
- Create statistics retrieval endpoints
- Implement statistics filtering and aggregation
- Add time-based statistics queries
- Create statistics export capabilities

**Iteration 3.2.3: Advanced Monitoring Features**
- Add real-time statistics updates
- Implement statistics alerting
- Create dashboard data endpoints
- Add performance trend analysis

#### Step 3.3: Error Handling and Logging

**Iteration 3.3.1: Structured Logging**
- Implement structured logging framework
- Create logging configuration
- Add context-aware logging
- Implement log level management

**Iteration 3.3.2: Error Handling Framework**
- Create standardized error responses
- Implement error classification
- Add error tracking and reporting
- Create error recovery mechanisms

**Iteration 3.3.3: Debugging and Monitoring**
- Add request/response tracing
- Implement performance profiling
- Create debugging endpoints
- Add system health monitoring

### Phase 4 Breakdown

#### Step 4.1: Testing Infrastructure

**Iteration 4.1.1: Unit Testing Setup**
- Set up pytest framework
- Create test fixtures and utilities
- Implement unit tests for core components
- Add test coverage reporting

**Iteration 4.1.2: Integration Testing**
- Create integration test scenarios
- Implement API endpoint testing
- Add configuration testing
- Create mock endpoint services

**Iteration 4.1.3: End-to-End Testing**
- Implement full system testing
- Create test scenarios for all features
- Add performance testing
- Implement automated test execution

#### Step 4.2: Dockerization and Deployment

**Iteration 4.2.1: Docker Configuration**
- Create Dockerfile and docker-compose
- Implement container health checks
- Add environment configuration
- Create container optimization

**Iteration 4.2.2: Deployment Automation**
- Create deployment scripts
- Implement CI/CD pipeline configuration
- Add deployment health validation
- Create rollback mechanisms

**Iteration 4.2.3: Production Monitoring**
- Set up monitoring and alerting
- Create production health dashboards
- Implement log aggregation
- Add performance monitoring

---

## LLM Implementation Prompts

### Prompt 1: Project Setup and Basic FastAPI Structure

```
Create a Python FastAPI orchestrating service project with the following requirements:

1. Set up a proper Python project structure with:
   - `pyproject.toml` for dependency management
   - Modular package structure under `src/orchestrator/`
   - Separate modules for: `config`, `registry`, `router`, `auth`, `health`, `stats`
   - Basic `main.py` as entry point

2. Implement a basic FastAPI application with:
   - Application factory pattern in `src/orchestrator/app.py`
   - Environment-based configuration loading
   - Basic error handling middleware
   - CORS configuration for development

3. Create the foundation for configuration management:
   - Pydantic models for endpoint configuration in `src/orchestrator/models.py`
   - Basic configuration loader in `src/orchestrator/config.py`
   - Configuration validation with proper error messages

4. Add development dependencies and setup:
   - pytest for testing
   - black and flake8 for code formatting
   - Basic test structure under `tests/`
   - Development scripts for running the application

Requirements:
- Use Python 3.9+
- Follow FastAPI best practices
- Include comprehensive docstrings
- Add basic logging setup
- Create a simple health check endpoint at `/health`

Ensure the application can start successfully and respond to basic requests. Include a sample configuration file structure but don't implement the full configuration loading yet.
```

### Prompt 2: Configuration Management System

```
Building on the previous FastAPI orchestrator setup, implement a comprehensive configuration management system:

1. Extend the Pydantic models in `src/orchestrator/models.py`:
   - `EndpointConfig` model with fields: url, name, version, methods, auth_type, disabled
   - `CircuitBreakerConfig` model with: failure_threshold, reset_timeout, fallback_strategy
   - `OrchestratorConfig` model that contains lists of endpoints and global settings
   - Add proper validation for URLs, HTTP methods, and required fields

2. Implement YAML configuration parsing in `src/orchestrator/config.py`:
   - `ConfigManager` class that loads and validates YAML configuration
   - Error handling for malformed YAML and validation errors
   - Configuration file watching using `watchdog` library
   - Automatic configuration reloading when file changes

3. Create configuration API endpoints in `src/orchestrator/config_api.py`:
   - `POST /config/reload` - manually trigger configuration reload
   - `GET /config/status` - get current configuration status and version
   - `GET /config/endpoints` - list all configured endpoints
   - Proper error responses for configuration errors

4. Add comprehensive testing:
   - Unit tests for configuration models and validation
   - Tests for YAML parsing with valid and invalid configurations
   - Tests for configuration reloading functionality
   - Mock file system tests for file watching

5. Create a sample `config.yaml` file with:
   - At least 3 sample endpoints with different configurations
   - Circuit breaker settings
   - Authentication settings
   - Proper documentation comments

Integration requirements:
- Wire the ConfigManager into the FastAPI app startup
- Add configuration validation at application startup
- Include proper logging for configuration changes
- Ensure configuration errors don't crash the application

The system should gracefully handle configuration errors and provide clear feedback about what went wrong.
```

### Prompt 3: Endpoint Registry Implementation

```
Continue building the FastAPI orchestrator by implementing the endpoint registry system:

1. Create `src/orchestrator/registry.py` with:
   - `EndpointRegistry` class for managing endpoint registration
   - In-memory storage using dictionaries for fast lookup
   - Methods: `register_endpoint()`, `unregister_endpoint()`, `get_endpoint()`, `list_endpoints()`
   - Support for endpoint versioning and conflict resolution
   - Thread-safe operations using appropriate locks

2. Extend endpoint models in `src/orchestrator/models.py`:
   - `RegisteredEndpoint` model that includes runtime information
   - Add fields: registration_time, last_health_check, status, circuit_breaker_state
   - `EndpointStatus` enum with values: ACTIVE, INACTIVE, DISABLED, UNHEALTHY
   - Methods for endpoint comparison and hashing

3. Implement registry API endpoints in `src/orchestrator/registry_api.py`:
   - `GET /registry/endpoints` - list all registered endpoints with filtering
   - `GET /registry/endpoints/{endpoint_id}` - get specific endpoint details
   - `POST /registry/endpoints` - manually register an endpoint
   - `DELETE /registry/endpoints/{endpoint_id}` - unregister an endpoint
   - Include pagination for listing endpoints

4. Integrate registry with configuration manager:
   - Automatically register endpoints from configuration on startup
   - Update registry when configuration is reloaded
   - Handle endpoint additions, updates, and removals
   - Maintain registry state during configuration changes

5. Add comprehensive testing:
   - Unit tests for registry operations
   - Tests for concurrent access and thread safety
   - Integration tests with configuration manager
   - API endpoint tests with various scenarios

6. Implement registry validation:
   - Check for duplicate endpoint URLs and names
   - Validate endpoint accessibility before registration
   - Handle registration failures gracefully
   - Provide detailed error messages for registration issues

Integration requirements:
- Wire the registry into the main application
- Add registry initialization during app startup
- Include proper error handling and logging
- Ensure registry state is consistent with configuration
- Add metrics for registry operations (registration count, active endpoints, etc.)

The registry should be the single source of truth for all endpoint information and handle dynamic changes efficiently.
```

### Prompt 4: Request Router Foundation

```
Implement the core request routing system for the FastAPI orchestrator:

1. Create `src/orchestrator/router.py` with:
   - `RequestRouter` class that handles dynamic request routing
   - Dynamic FastAPI route generation based on registered endpoints
   - HTTP client setup using `httpx` for making requests to target endpoints
   - Request/response forwarding with header preservation
   - Proper handling of different HTTP methods (GET, POST, PUT, DELETE, PATCH)

2. Implement routing logic:
   - Match incoming requests to registered endpoints
   - Support for path parameters and query parameters forwarding
   - Request body forwarding for POST/PUT requests
   - Response streaming for large responses
   - Timeout handling for target endpoint requests

3. Create `src/orchestrator/proxy.py` for request forwarding:
   - `EndpointProxy` class for making requests to target endpoints
   - Header filtering and forwarding (preserve authentication, content-type, etc.)
   - Request transformation if needed
   - Response code and header preservation
   - Error handling for network issues and timeouts

4. Add router API endpoints in `src/orchestrator/router_api.py`:
   - `GET /router/routes` - list all active routes
   - `GET /router/test/{endpoint_id}` - test connectivity to an endpoint
   - `POST /router/refresh` - refresh route mappings
   - Include route debugging information

5. Integrate with endpoint registry:
   - Automatically create routes for registered endpoints
   - Update routes when registry changes
   - Remove routes for unregistered endpoints
   - Handle endpoint URL changes

6. Implement comprehensive testing:
   - Unit tests for routing logic
   - Mock endpoint servers for testing
   - Integration tests with real HTTP requests
   - Test various HTTP methods and status codes
   - Test error scenarios (timeout, connection refused, etc.)

7. Add request/response middleware:
   - Request logging with unique request IDs
   - Response time measurement
   - Basic request validation
   - Error response standardization

Integration requirements:
- Wire the router into the main FastAPI application
- Add route generation during application startup
- Include proper error handling for routing failures
- Add metrics for request routing (success/failure rates, response times)
- Ensure routes are dynamically updated when configuration changes

The router should efficiently handle concurrent requests and provide clear error messages when endpoints are unreachable.
```

### Prompt 5: Health Check System

```
Implement a comprehensive health check system for the FastAPI orchestrator:

1. Create `src/orchestrator/health.py` with:
   - `HealthChecker` class for managing endpoint health checks
   - `EndpointHealth` model with status, last_check_time, response_time, error_message
   - Configurable health check intervals and timeouts
   - Support for different health check types (HTTP GET, custom endpoints)
   - Asynchronous health checking using `asyncio`

2. Implement health check logic:
   - Periodic health checks running in background tasks
   - Configurable health check endpoints per target endpoint
   - Response time tracking and SLA monitoring
   - Health status persistence and history tracking
   - Exponential backoff for failed health checks

3. Create health check scheduling in `src/orchestrator/scheduler.py`:
   - Background task scheduler using FastAPI background tasks
   - Configurable check intervals based on endpoint status
   - Priority-based scheduling (unhealthy endpoints checked more frequently)
   - Graceful shutdown handling for background tasks

4. Add health monitoring API in `src/orchestrator/health_api.py`:
   - `GET /health/status` - overall system health
   - `GET /health/endpoints` - health status of all endpoints
   - `GET /health/endpoints/{endpoint_id}` - specific endpoint health
   - `POST /health/check/{endpoint_id}` - trigger manual health check
   - Include health history and trends

5. Integrate with endpoint registry:
   - Update endpoint status based on health checks
   - Mark endpoints as unhealthy/healthy in registry
   - Trigger registry updates when health status changes
   - Remove unhealthy endpoints from active routing (optional)

6. Implement health check configuration:
   - Per-endpoint health check settings in configuration
   - Global health check defaults
   - Custom health check URLs and expected responses
   - Health check timeout and retry configurations

7. Add comprehensive testing:
   - Unit tests for health check logic
   - Mock endpoint responses for testing
   - Test health check scheduling and intervals
   - Integration tests with real endpoint health checks
   - Test health status persistence and updates

8. Create health check notifications:
   - Log health status changes
   - Optional webhook notifications for health changes
   - Health check metrics collection
   - Alert thresholds for consecutive failures

Integration requirements:
- Start health check scheduler during application startup
- Integrate health status with endpoint registry
- Add health check metrics to statistics system
- Ensure health checks don't impact application performance
- Include proper error handling and logging for health check failures

The health check system should provide real-time visibility into endpoint availability and help identify issues before they impact users.
```

### Prompt 6: Circuit Breaker Implementation

```
Implement a circuit breaker pattern for fault tolerance in the FastAPI orchestrator:

1. Create `src/orchestrator/circuit_breaker.py` with:
   - `CircuitBreaker` class implementing the circuit breaker pattern
   - Three states: CLOSED, OPEN, HALF_OPEN with proper state transitions
   - Configurable failure threshold and reset timeout
   - Failure counting and time window management
   - Thread-safe operations for concurrent access

2. Implement circuit breaker logic:
   - Failure tracking with sliding window or consecutive failure counting
   - Automatic state transitions based on failure thresholds
   - Half-open state testing with limited requests
   - Success/failure ratio monitoring
   - Configurable recovery strategies

3. Create fallback strategies in `src/orchestrator/fallback.py`:
   - `FallbackHandler` class with different fallback strategies
   - Strategies: return cached response, default response, error response, redirect
   - Configurable fallback responses per endpoint
   - Cache integration for cached response fallbacks

4. Add circuit breaker configuration:
   - Per-endpoint circuit breaker settings in configuration
   - Global circuit breaker defaults
   - Configurable failure thresholds, timeouts, and strategies
   - Dynamic configuration updates for circuit breaker parameters

5. Integrate with request router:
   - Check circuit breaker state before routing requests
   - Execute fallback strategies when circuit is open
   - Record request results in circuit breaker
   - Update circuit breaker state based on request outcomes

6. Create circuit breaker API in `src/orchestrator/circuit_breaker_api.py`:
   - `GET /circuit-breaker/status` - overall circuit breaker status
   - `GET /circuit-breaker/endpoints/{endpoint_id}` - specific endpoint circuit state
   - `POST /circuit-breaker/reset/{endpoint_id}` - manually reset circuit breaker
   - `POST /circuit-breaker/trip/{endpoint_id}` - manually trip circuit breaker

7. Implement circuit breaker metrics:
   - Track state transitions and timing
   - Count failures, successes, and fallback usage
   - Measure circuit breaker effectiveness
   - Include metrics in statistics API

8. Add comprehensive testing:
   - Unit tests for circuit breaker state machine
   - Test failure threshold and timeout behaviors
   - Integration tests with request router
   - Test fallback strategy execution
   - Mock endpoint failures for testing

9. Integrate with health check system:
   - Use health check results to inform circuit breaker decisions
   - Coordinate circuit breaker state with endpoint health status
   - Reset circuit breakers when endpoints become healthy
   - Include circuit breaker state in health reports

Integration requirements:
- Wire circuit breakers into the request routing flow
- Initialize circuit breakers for all registered endpoints
- Include circuit breaker state in endpoint registry
- Add circuit breaker metrics to monitoring system
- Ensure circuit breaker decisions are made quickly to avoid blocking requests

The circuit breaker should prevent cascading failures and provide graceful degradation when endpoints are experiencing issues.
```

### Prompt 7: Authentication and Authorization

```
Implement JWT-based authentication and authorization for the FastAPI orchestrator:

1. Create `src/orchestrator/auth.py` with:
   - `AuthManager` class for JWT token handling
   - JWT token validation, parsing, and verification
   - Support for multiple JWT algorithms (RS256, HS256)
   - Token expiration and signature validation
   - User context extraction from tokens

2. Implement authentication middleware in `src/orchestrator/middleware.py`:
   - FastAPI dependency for JWT authentication
   - Optional authentication for specific endpoints
   - Authentication bypass for health check endpoints
   - Request context enrichment with user information
   - Authentication error handling with proper HTTP status codes

3. Create authorization system:
   - Role-based access control (RBAC) model
   - Permission definitions for different operations
   - Endpoint-specific authorization rules
   - Admin vs. user access levels
   - Resource-based permissions

4. Add authentication configuration:
   - JWT secret key and algorithm configuration
   - Token issuer and audience validation
   - Authentication requirements per endpoint
   - Optional authentication for development mode

5. Implement secure endpoints in `src/orchestrator/auth_api.py`:
   - `POST /auth/validate` - validate JWT token
   - `GET /auth/user` - get current user information
   - `POST /auth/refresh` - refresh authentication token (if supported)
   - Protected admin endpoints for orchestrator management

6. Integrate authentication with existing APIs:
   - Protect configuration management endpoints
   - Secure registry management operations
   - Add authentication to statistics and monitoring APIs
   - Protect circuit breaker control endpoints

7. Add JWT utilities:
   - Token parsing and validation functions
   - User role and permission checking
   - Token expiration handling
   - Development mode token generation for testing

8. Implement comprehensive testing:
   - Unit tests for JWT validation and parsing
   - Test authentication middleware with valid/invalid tokens
   - Authorization tests for different user roles
   - Integration tests with protected endpoints
   - Test authentication bypass scenarios

9. Add security features:
   - Rate limiting for authentication attempts
   - Request logging for security auditing
   - Token blacklisting support (optional)
   - Security headers in responses

10. Create authentication documentation:
    - JWT token format requirements
    - Required claims and their meanings
    - Authentication error response formats
    - Examples of valid authentication headers

Integration requirements:
- Apply authentication middleware to appropriate endpoints
- Integrate with existing API endpoints
- Add authentication context to request logging
- Include authentication metrics in statistics
- Ensure authentication doesn't significantly impact performance

The authentication system should be secure, performant, and provide clear error messages for authentication failures.
```

### Prompt 8: Statistics and Monitoring API

```
Implement comprehensive statistics and monitoring capabilities for the FastAPI orchestrator:

1. Create `src/orchestrator/statistics.py` with:
   - `StatisticsCollector` class for gathering metrics
   - Real-time metrics collection for requests, responses, and errors
   - Performance metrics (response times, throughput, error rates)
   - Endpoint-specific statistics tracking
   - Time-based aggregation (hourly, daily statistics)

2. Implement metrics collection:
   - Request/response middleware for automatic metrics collection
   - Circuit breaker state change tracking
   - Health check result tracking
   - Authentication success/failure rates
   - Resource usage monitoring (memory, CPU if needed)

3. Create statistics storage in `src/orchestrator/metrics_store.py`:
   - In-memory metrics storage with efficient data structures
   - Time-series data storage for historical metrics
   - Configurable data retention policies
   - Metrics aggregation and summarization
   - Thread-safe metrics updates

4. Add statistics models in `src/orchestrator/models.py`:
   - `EndpointStatistics` model with comprehensive metrics
   - `SystemStatistics` model for overall system health
   - `MetricPoint` model for time-series data
   - Request/response statistics models

5. Implement statistics API in `src/orchestrator/stats_api.py`:
   - `GET /stats/system` - overall system statistics
   - `GET /stats/endpoints` - statistics for all endpoints
   - `GET /stats/endpoints/{endpoint_id}` - specific endpoint statistics
   - `GET /stats/endpoints/{endpoint_id}/history` - historical data
   - Support for time range filtering and aggregation

6. Add monitoring dashboard endpoints:
   - `GET /stats/dashboard` - dashboard data for monitoring tools
   - `GET /stats/health-summary` - health status summary
   - `GET /stats/performance` - performance metrics summary
   - Real-time statistics with Server-Sent Events (optional)

7. Implement metrics export:
   - Prometheus metrics export endpoint (`/metrics`)
   - JSON metrics export for external monitoring tools
   - Configurable metrics filtering and labels
   - Custom metrics definitions

8. Add comprehensive testing:
   - Unit tests for statistics collection
   - Test metrics aggregation and storage
   - API endpoint tests for statistics retrieval
   - Performance tests for metrics collection overhead
   - Test historical data accuracy

9. Integrate with existing systems:
   - Collect metrics from request router
   - Include circuit breaker statistics
   - Track health check results and trends
   - Monitor authentication success rates
   - Include configuration reload events

10. Create alerting foundation:
    - Threshold-based alerting rules
    - Metrics comparison and trend analysis
    - Alert notification system (webhooks, email)
    - Alert escalation and acknowledgment

11. Add statistics configuration:
    - Configurable metrics collection intervals
    - Data retention policies
    - Metrics export settings
    - Alert thresholds and rules

Integration requirements:
- Integrate statistics collection into all major components
- Add metrics middleware to the FastAPI application
- Include statistics in application startup and health checks
- Ensure statistics collection doesn't impact application performance
- Make statistics API available for monitoring tools and dashboards

The statistics system should provide comprehensive visibility into system performance and help identify trends and issues.
```

### Prompt 9: Error Handling and Logging

```
Implement comprehensive error handling and logging throughout the FastAPI orchestrator:

1. Create `src/orchestrator/logging_config.py` with:
   - Structured logging configuration using Python's logging module
   - JSON log formatting for production environments
   - Configurable log levels and handlers
   - Log rotation and file management
   - Request correlation ID generation and tracking

2. Implement error handling framework in `src/orchestrator/errors.py`:
   - Custom exception classes for different error types
   - `OrchestratorException` base class with error codes
   - Specific exceptions: `ConfigurationError`, `EndpointError`, `AuthenticationError`, etc.
   - Error response models with consistent structure
   - HTTP status code mapping for different error types

3. Create error middleware in `src/orchestrator/middleware.py`:
   - Global exception handler for unhandled exceptions
   - Structured error response generation
   - Error logging with full context and stack traces
   - Request/response logging for debugging
   - Performance monitoring and slow request detection

4. Add context-aware logging:
   - Request context injection into log messages
   - User context and authentication information in logs
   - Endpoint and operation context tracking
   - Correlation ID propagation across components
   - Structured log fields for easy parsing

5. Implement error recovery mechanisms:
   - Retry logic with exponential backoff
   - Graceful degradation strategies
   - Error notification and alerting
   - Automatic error recovery where possible

6. Create debugging utilities in `src/orchestrator/debug.py`:
   - Request/response tracing capabilities
   - Performance profiling endpoints
   - Debug information collection
   - System state inspection endpoints
   - Memory and resource usage monitoring

7. Add operational endpoints:
   - `GET /debug/logs` - recent log entries (admin only)
   - `GET /debug/errors` - recent errors and their frequency
   - `GET /debug/performance` - performance debugging information
   - `POST /debug/log-level` - dynamic log level adjustment

8. Implement log aggregation preparation:
   - Structured logging for external log aggregation tools
   - Log shipping configuration (for ELK stack, etc.)
   - Log sampling for high-volume environments
   - Log filtering and redaction for sensitive data

9. Add comprehensive testing:
   - Unit tests for custom exceptions and error handling
   - Test error middleware with various exception types
   - Integration tests for error scenarios
   - Test log output format and content
   - Performance tests for logging overhead

10. Create monitoring integration:
    - Error rate monitoring and alerting
    - Log-based metrics and dashboards
    - Error trend analysis
    - Integration with external monitoring tools

11. Add security considerations:
    - Sensitive data redaction in logs
    - Log access control and security
    - Audit logging for security events
    - Log integrity and tamper detection

12. Implement error documentation:
    - Error code documentation
    - Troubleshooting guides
    - Log analysis guides
    - Error response examples

Integration requirements:
- Apply error handling to all existing components
- Add logging to all major operations and state changes
- Integrate error metrics with statistics system
- Ensure error handling doesn't mask important exceptions
- Provide clear error messages for API consumers
- Include proper cleanup in error scenarios

The error handling and logging system should provide comprehensive visibility into system behavior and help diagnose issues quickly.
```

### Prompt 10: Testing Infrastructure

```
Implement comprehensive testing infrastructure for the FastAPI orchestrator:

1. Set up testing framework in `tests/` directory:
   - Configure pytest with proper test discovery
   - Set up test fixtures and utilities
   - Create test configuration and environment setup
   - Add test database/storage setup (if needed)
   - Configure test coverage reporting

2. Create unit tests in `tests/unit/`:
   - `test_config.py` - configuration management tests
   - `test_registry.py` - endpoint registry tests
   - `test_router.py` - request routing tests
   - `test_circuit_breaker.py` - circuit breaker logic tests
   - `test_auth.py` - authentication and authorization tests
   - `test_health.py` - health check system tests
   - `test_statistics.py` - metrics collection tests

3. Implement integration tests in `tests/integration/`:
   - `test_api_endpoints.py` - API endpoint integration tests
   - `test_configuration_flow.py` - end-to-end configuration tests
   - `test_request_routing.py` - request routing integration tests
   - `test_health_monitoring.py` - health check integration tests
   - `test_auth_flow.py` - authentication flow tests

4. Create test utilities in `tests/utils/`:
   - `mock_endpoints.py` - mock HTTP servers for testing
   - `test_fixtures.py` - reusable test fixtures
   - `test_data.py` - test configuration and data
   - `auth_helpers.py` - JWT token generation for tests
   - `assertion_helpers.py` - custom assertions for testing

5. Add end-to-end tests in `tests/e2e/`:
   - `test_full_flow.py` - complete orchestrator workflow tests
   - `test_performance.py` - performance and load tests
   - `test_fault_tolerance.py` - circuit breaker and error handling tests
   - `test_configuration_scenarios.py` - various configuration scenarios

6. Implement test data management:
   - Sample configuration files for different test scenarios
   - Test endpoint configurations with various auth types
   - Mock JWT tokens with different permissions
   - Test health check scenarios and responses

7. Create performance testing:
   - Load testing with concurrent requests
   - Performance benchmarks for routing decisions
   - Memory usage and leak detection
   - Response time analysis under load

8. Add test automation:
   - GitHub Actions or similar CI/CD configuration
   - Automated test execution on code changes
   - Test coverage reporting and enforcement
   - Integration with code quality tools

9. Implement test environment setup:
   - Docker containers for isolated testing
   - Test database setup and teardown
   - Mock external services for testing
   - Test configuration management

10. Create test documentation:
    - Testing strategy and guidelines
    - How to run different test suites
    - Test data and fixture documentation
    - Troubleshooting test failures

11. Add specialized testing scenarios:
    - Network failure simulation
    - Configuration error handling
    - Authentication failure scenarios
    - Circuit breaker state transitions
    - Health check failure recovery

12. Implement test metrics and reporting:
    - Test execution time tracking
    - Test failure analysis and reporting
    - Coverage reports with missing areas highlighted
    - Performance regression detection

Integration requirements:
- Ensure all existing components have adequate test coverage
- Add tests for error scenarios and edge cases
- Include tests for concurrent operations
- Test configuration changes and reloading
- Validate API contracts and response formats
- Test authentication and authorization thoroughly

The testing infrastructure should provide confidence in system reliability and catch regressions early in the development process.
```

### Prompt 11: Dockerization and Deployment

```
Create comprehensive Docker and deployment configuration for the FastAPI orchestrator:

1. Create `Dockerfile` with:
   - Multi-stage build for optimized production image
   - Python 3.9+ base image with minimal security vulnerabilities
   - Proper dependency installation and caching
   - Non-root user setup for security
   - Health check configuration
   - Proper signal handling for graceful shutdown

2. Implement `docker-compose.yml` for development:
   - Orchestrator service with environment configuration
   - Optional dependencies (Redis for caching, if used)
   - Volume mounts for configuration files
   - Development environment variables
   - Port mapping and networking setup

3. Create production deployment configuration:
   - `docker-compose.prod.yml` for production deployment
   - Environment-specific configuration management
   - Secrets management for JWT keys and sensitive data
   - Resource limits and health checks
   - Logging configuration for production

4. Add container health checks in `src/orchestrator/health_endpoints.py`:
   - `/health/live` - liveness probe endpoint
   - `/health/ready` - readiness probe endpoint
   - `/health/startup` - startup probe endpoint
   - Comprehensive health validation including dependencies

5. Implement deployment scripts in `scripts/`:
   - `deploy.sh` - deployment automation script
   - `backup.sh` - configuration and data backup
   - `rollback.sh` - deployment rollback capabilities
   - `health-check.sh` - post-deployment validation

6. Create Kubernetes manifests in `k8s/` (optional):
   - Deployment configuration with rolling updates
   - Service and ingress configuration
   - ConfigMap for configuration files
   - Secrets for sensitive configuration
   - HorizontalPodAutoscaler for scaling

7. Add monitoring and observability:
   - Prometheus metrics endpoint configuration
   - Log shipping configuration (fluentd, filebeat)
   - Health check monitoring setup
   - Performance monitoring integration

8. Implement configuration management for deployment:
   - Environment-specific configuration files
   - Configuration validation at startup
   - Secret injection from environment variables
   - Configuration hot-reloading in containers

9. Create CI/CD pipeline configuration in `.github/workflows/`:
   - Automated testing on pull requests
   - Docker image building and pushing
   - Security scanning of container images
   - Automated deployment to staging/production

10. Add security hardening:
    - Container image vulnerability scanning
    - Non-root user execution
    - Read-only root filesystem where possible
    - Minimal container attack surface
    - Security context configuration

11. Implement backup and recovery:
    - Configuration backup strategies
    - State recovery procedures
    - Disaster recovery planning
    - Data persistence configuration

12. Create operational documentation:
    - Deployment runbook and procedures
    - Troubleshooting guides
    - Monitoring and alerting setup
    - Scaling and performance tuning guides

13. Add production optimizations:
    - Multi-worker configuration for high load
    - Resource usage optimization
    - Connection pooling and timeouts
    - Caching strategies for improved performance

Integration requirements:
- Ensure all application components work in containerized environment
- Test container builds and deployments
- Validate health checks work correctly
- Include proper logging and monitoring
- Ensure graceful shutdown and startup
- Test configuration loading from environment variables

The deployment configuration should provide a production-ready, scalable, and maintainable deployment solution for the orchestrator service.
```

---

## Final Integration and Documentation Prompt

```
Create the final integration, documentation, and production readiness for the FastAPI orchestrator:

1. Finalize application integration in `src/orchestrator/app.py`:
   - Wire all components together in the application factory
   - Ensure proper startup and shutdown sequences
   - Add comprehensive application health checks
   - Implement graceful degradation for component failures

2. Create comprehensive API documentation:
   - Complete OpenAPI/Swagger documentation
   - API usage examples and tutorials
   - Authentication setup instructions
   - Configuration reference documentation

3. Add production configuration templates:
   - Production-ready `config.yaml` template
   - Environment variable configuration guide
   - Security configuration recommendations
   - Performance tuning guidelines

4. Implement final testing and validation:
   - End-to-end system validation tests
   - Performance benchmarking suite
   - Security validation and penetration testing
   - Load testing scenarios

5. Create operational documentation:
   - Installation and setup guide
   - Operation and maintenance procedures
   - Troubleshooting and debugging guide
   - Monitoring and alerting setup

6. Add final polish and optimization:
   - Code review and cleanup
   - Performance optimization
   - Security hardening verification
   - Documentation completeness check

Ensure the final system is production-ready, well-documented, and thoroughly tested. All components should work together seamlessly, and the system should be ready for deployment in a production environment.
``` 