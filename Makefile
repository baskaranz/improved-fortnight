# Makefile for Orchestrator API Docker operations

.PHONY: help build run run-dev stop clean logs test health

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build the Docker image"
	@echo "  run       - Run the orchestrator in production mode"
	@echo "  run-dev   - Run the orchestrator in development mode with hot reload"
	@echo "  stop      - Stop all running containers"
	@echo "  clean     - Stop containers and remove images"
	@echo "  logs      - Show container logs"
	@echo "  health    - Check service health"
	@echo "  test      - Run tests in container"
	@echo "  shell     - Open shell in running container"

# Build the Docker image
build:
	docker-compose build orchestrator

# Run in production mode
run:
	docker-compose up -d orchestrator
	@echo "Orchestrator is running at http://localhost:8000"
	@echo "API documentation: http://localhost:8000/docs"

# Run in development mode with hot reload
run-dev:
	docker-compose --profile dev up -d orchestrator-dev
	@echo "Orchestrator (dev mode) is running at http://localhost:8000"
	@echo "API documentation: http://localhost:8000/docs"

# Stop all containers
stop:
	docker-compose down

# Clean up containers and images
clean:
	docker-compose down --rmi all --volumes --remove-orphans

# Show container logs
logs:
	docker-compose logs -f orchestrator

# Show development container logs
logs-dev:
	docker-compose logs -f orchestrator-dev

# Check service health
health:
	@echo "Checking orchestrator health..."
	@curl -f http://localhost:8000/health || echo "Service is not healthy"
	@echo ""
	@echo "Checking endpoint health..."
	@curl -f http://localhost:8000/health/status || echo "Could not get status"

# Run tests in container
test:
	docker-compose exec orchestrator python -m pytest tests/ -v

# Open shell in running container
shell:
	docker-compose exec orchestrator /bin/bash

# Quick setup for new developers
setup:
	@echo "Setting up orchestrator development environment..."
	docker-compose build
	docker-compose --profile dev up -d orchestrator-dev
	@echo "Development environment ready at http://localhost:8000"
	@echo "API docs: http://localhost:8000/docs"

# Build and run in one command
up: build run

# Build and run dev in one command
up-dev: build run-dev 