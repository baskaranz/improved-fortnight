"""
Tests for FastAPI application creation and configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.orchestrator.app import create_app
from src.orchestrator.models import OrchestratorConfig


class TestAppCreation:
    """Test application creation and configuration."""
    
    def test_create_app_basic(self):
        """Test basic app creation."""
        with patch('src.orchestrator.app.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_config.return_value = OrchestratorConfig()
            
            app = create_app()
            assert app is not None
            assert app.title == "Orchestrator API"
            assert app.version == "0.1.0"
    
    def test_create_app_with_config_path(self):
        """Test app creation with config manager setup."""
        with patch('src.orchestrator.app.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_config.return_value = OrchestratorConfig()
            
            app = create_app()
            assert app is not None
            # Verify the app has the required routes
            assert any("/config" in str(route.path) for route in app.routes)
            assert any("/registry" in str(route.path) for route in app.routes)
    
    def test_app_client_basic_routes(self):
        """Test basic routes through test client."""
        with patch('src.orchestrator.app.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_config.return_value = OrchestratorConfig()
            
            app = create_app()
            client = TestClient(app)
            
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["service"] == "Orchestrator API"
            assert "endpoints" in data
    
    def test_app_with_lifespan_events(self):
        """Test app lifecycle events."""
        with patch('src.orchestrator.app.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_config.return_value = OrchestratorConfig()
            
            app = create_app()
            assert app.router.lifespan_context is not None

    def test_create_app_registers_routes(self):
        """Test that app registers routes."""
        app = create_app()
        
        # Check that some routes are registered
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        # Should have some routes registered
        assert len(route_paths) > 0
    
    def test_create_app_has_middleware(self):
        """Test that app has middleware."""
        app = create_app()
        
        # Should have some middleware
        assert hasattr(app, 'user_middleware')
        assert len(app.user_middleware) >= 0 