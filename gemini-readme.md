# Yet Another Orchestrator API - Architecture

## 1. Introduction

This document outlines the architecture of the **Yet Another Orchestrator API**, a Python-based orchestrating service built with FastAPI. The service acts as a dynamic and scalable API gateway, routing incoming requests to various backend services (endpoints). It is designed to be configuration-driven, resilient, and observable.

The key features of the orchestrator include:

-   **Dynamic Routing:** Endpoints are registered dynamically from a configuration file, and the orchestrator routes requests to them based on the request path.
-   **Configuration Management:** The service loads its configuration from a YAML file and can reload it on the fly without a restart.
-   **Health Checks:** It actively monitors the health of registered endpoints and can mark them as unhealthy if they fail to respond correctly.
-   **Circuit Breaker:** Implements the circuit breaker pattern to prevent cascading failures when an endpoint is down.
-   **Authentication and Authorization:** Secures its own management APIs using JWT-based authentication and role-based access control (RBAC).
-   **Metrics and Statistics:** Collects detailed metrics on requests, response times, and errors, providing insights into the performance of the system and its endpoints.

## 2. High-Level Architecture

The orchestrator is a single FastAPI application that can be deployed as a standalone service. It sits between clients and a set of backend services, proxying requests to the appropriate service based on its configuration.

The architecture is modular, with each major concern handled by a dedicated component. The core components are:

-   **FastAPI Application (`app.py`):** The main entry point of the service. It initializes all other components and sets up the application lifecycle (startup and shutdown events).
-   **Configuration Manager (`config.py`):** Responsible for loading, validating, and watching the `config.yaml` file for changes.
-   **Endpoint Registry (`registry.py`):** An in-memory store of all registered endpoints. It's the single source of truth for which endpoints are available and their current status.
-   **Request Router (`router.py`):** The component that handles incoming requests to the `/orchestrator/{path:path}` endpoint, determines the correct backend service to forward the request to, and proxies the request.
-   **Health Checker (`health.py`):** A background task that periodically checks the health of all registered endpoints.
-   **Circuit Breaker Manager (`circuit_breaker.py`):** Manages the state of circuit breakers for each endpoint.
-   **Authentication Manager (`auth.py`):** Handles JWT creation and verification for securing the management APIs.
-   **Metrics Collector (`statistics.py`):** Gathers and aggregates statistics about the requests being processed.

These components are tied together in the `app.py` module, which creates instances of each and makes them available to the API endpoints through dependency injection.

## 3. Component Deep Dive

### 3.1. FastAPI Application (`app.py`)

-   **Framework:** Built on [FastAPI](https://fastapi.tiangolo.com/), which provides high performance, automatic API documentation (Swagger UI and ReDoc), and a modern developer experience.
-   **Application Lifecycle:** Uses FastAPI's `lifespan` context manager to initialize all the core components on startup and gracefully shut them down on exit. This ensures that background tasks like the health checker and file watcher are properly managed.
-   **API Routers:** The application is organized into several API routers, each corresponding to a major feature (e.g., `config_api.py`, `registry_api.py`). This keeps the API definitions clean and modular.
-   **Global Instances:** The core components (ConfigManager, EndpointRegistry, etc.) are instantiated as global singletons within the `app.py` module. Dependency injection functions (`get_config_manager`, `get_registry`, etc.) are provided to make these instances available to the API endpoints.
-   **Catch-All Route:** The main orchestration logic is handled by a catch-all route: `@app.api_route("/orchestrator/{path:path}", ...)` This route captures all requests to the `/orchestrator/` path and passes them to the `RequestRouter`.
-   **Middleware:**
    -   **CORS:** `CORSMiddleware` is used to allow cross-origin requests.
    -   **Request ID:** A custom middleware adds a unique `X-Request-ID` header to every request and response, which is useful for tracing and logging.
    -   **Global Exception Handler:** A global exception handler catches any unhandled exceptions and returns a standardized JSON error response.

### 3.2. Configuration (`config.py` and `config.yaml`)

-   **Configuration File:** The service is configured via a YAML file (`config/config.yaml`). This file defines the endpoints, circuit breaker settings, health check parameters, and other operational settings.
-   **Pydantic Models:** The configuration is parsed and validated using Pydantic models (`models.py`). This ensures that the configuration is well-formed and provides type safety. The main configuration model is `OrchestratorConfig`.
-   **Hot Reloading:** The `ConfigManager` uses the `watchdog` library to monitor the configuration file for changes. When the file is modified, the `ConfigManager` automatically reloads the configuration and triggers callbacks to notify other components (like the `EndpointRegistry`) of the changes.

### 3.3. Endpoint Registry (`registry.py`)

-   **In-Memory Store:** The `EndpointRegistry` is an in-memory dictionary that stores `RegisteredEndpoint` objects. Each object contains the endpoint's configuration and its current runtime state (status, health check info, etc.).
-   **Synchronization with Config:** The registry is kept in sync with the `config.yaml` file. When the configuration is reloaded, the registry adds, updates, or removes endpoints to match the new configuration.
-   **Status Tracking:** The registry is the central place where the status of each endpoint is tracked. Other components, like the `HealthChecker` and `CircuitBreakerManager`, update the endpoint's status in the registry.

### 3.4. Request Router (`router.py`)

-   **Dynamic Routing Logic:** The `RequestRouter` is responsible for the core orchestration logic. When a request comes in, it:
    1.  Finds the best-matching endpoint from its route cache based on the request path. The matching is done by looking for prefixes that correspond to the endpoint's `name` and `version`.
    2.  Performs checks to ensure the endpoint is not disabled, unhealthy, or has an open circuit breaker.
    3.  Checks if the HTTP method is allowed for the endpoint.
    4.  Forwards the request to the endpoint's URL using the `httpx` library.
-   **HTTPX Client:** It uses an `httpx.AsyncClient` to make asynchronous HTTP requests to the backend services, which is essential for high performance.
-   **Header Filtering:** It filters out hop-by-hop headers before forwarding the request and response.

### 3.5. Health Checker (`health.py`)

-   **Background Task:** The `HealthChecker` runs as a background `asyncio` task that periodically sends requests to the health check path of each registered endpoint.
-   **Health Status:** Based on the response from the health check, it updates the endpoint's status in the `EndpointRegistry`. It uses a thresholding mechanism (e.g., an endpoint is marked as unhealthy after 3 consecutive failures) to avoid flapping.
-   **Asynchronous Checks:** It performs health checks concurrently for all endpoints to minimize the time it takes to complete a health check cycle.

### 3.6. Circuit Breaker (`circuit_breaker.py`)

-   **Fault Tolerance:** The `CircuitBreakerManager` implements the circuit breaker pattern to prevent the orchestrator from repeatedly trying to call a service that is known to be failing.
-   **States:** Each endpoint has a circuit breaker that can be in one of three states: `CLOSED`, `OPEN`, or `HALF_OPEN`.
-   **State Transitions:**
    -   If the number of failures for an endpoint exceeds a threshold, the circuit breaker "opens," and further calls to that endpoint are blocked for a configured timeout.
    -   After the timeout, the circuit breaker transitions to the `HALF_OPEN` state, allowing a limited number of test requests through.
    -   If the test requests succeed, the circuit breaker "closes," and normal operation resumes. If they fail, it goes back to the `OPEN` state.
-   **Fallback Strategies:** When the circuit is open, it can be configured to return an error, a cached response, or a default response.

### 3.7. Authentication and Authorization (`auth.py` and `middleware.py`)

-   **JWT-based:** The management APIs are secured using JSON Web Tokens (JWT).
-   **AuthManager:** The `AuthManager` class is responsible for creating and verifying JWTs.
-   **Role-Based Access Control (RBAC):** The system defines roles (e.g., `admin`, `user`, `readonly`) and permissions (e.g., `config:read`, `registry:write`). API endpoints can be protected by requiring a specific role or permission.
-   **Middleware and Dependencies:** Authentication is enforced using FastAPI dependencies (`Depends`) that check for a valid JWT in the `Authorization` header.

### 3.8. Statistics and Metrics (`statistics.py`)

-   **Metrics Collector:** The `MetricsCollector` is responsible for collecting and aggregating various metrics, including:
    -   Request counts (total, successful, failed)
    -   Average response times
    -   Circuit breaker trips
-   **In-Memory Storage:** Metrics are stored in memory. The `MetricsCollector` keeps both summary statistics and time-series data in a `deque` for a configurable retention period.
-   **Prometheus Exporter:** It includes an endpoint (`/stats/metrics`) that exposes the metrics in the Prometheus format, allowing for easy integration with Prometheus and Grafana for monitoring and visualization.

## 4. Data Models (`models.py`)

The service uses Pydantic models extensively to define the structure of its data. This includes:

-   **Configuration Models:** `OrchestratorConfig`, `EndpointConfig`, `HealthCheckConfig`, etc.
-   **Runtime Models:** `RegisteredEndpoint`, `EndpointHealth`, `EndpointStatistics`.
-   **API Models:** Request and response models for the API endpoints.
-   **Enums:** Enumerations for things like `HTTPMethod`, `EndpointStatus`, and `CircuitBreakerState`.

Using Pydantic provides data validation, serialization, and automatic generation of JSON Schema for the API documentation.

## 5. Directory Structure

The project follows a standard Python project structure:

-   `src/orchestrator/`: The main source code for the application.
    -   `app.py`: The main FastAPI application.
    -   `*.py`: The core components (router, registry, etc.).
    -   `*_api.py`: The API route definitions.
-   `config/`: Contains the configuration files.
-   `tests/`: Contains the tests for the application.
-   `pyproject.toml`: Defines the project metadata and dependencies.

## 6. Conclusion

The Yet Another Orchestrator API is a well-structured, modular, and extensible service. Its use of FastAPI, Pydantic, and asynchronous programming makes it performant and modern. The architecture is designed for resilience and observability, with features like health checks, circuit breakers, and metrics collection being integral parts of the system. The configuration-driven approach allows for easy management and dynamic updates of the orchestrated endpoints.
