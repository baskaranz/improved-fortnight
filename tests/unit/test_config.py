"""
Unit tests for configuration management.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.orchestrator.config import ConfigManager
from src.orchestrator.models import OrchestratorConfig, EndpointConfig


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "endpoints": [
                {
                    "url": "https://httpbin.org/get",
                    "name": "test_endpoint",
                    "methods": ["GET"],
                    "auth_type": "none"
                }
            ],
            "log_level": "INFO"
        }
        yaml.dump(config_data, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def config_manager(temp_config_file):
    """Create a config manager with temporary file."""
    return ConfigManager(temp_config_file)


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    @pytest.mark.asyncio
    async def test_load_valid_config(self, config_manager):
        """Test loading a valid configuration file."""
        config = await config_manager.load_config()
        
        assert isinstance(config, OrchestratorConfig)
        assert len(config.endpoints) == 1
        assert config.endpoints[0].name == "test_endpoint"
        assert config.log_level == "INFO"
    
    @pytest.mark.asyncio
    async def test_load_missing_config_creates_default(self):
        """Test that missing config file creates default configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing_config.yaml"
            config_manager = ConfigManager(str(config_path))
            
            config = await config_manager.load_config()
            
            assert isinstance(config, OrchestratorConfig)
            assert config_path.exists()
            assert len(config.endpoints) == 0  # Default config has no endpoints
    
    @pytest.mark.asyncio
    async def test_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            config_manager = ConfigManager(f.name)
            
            with pytest.raises(Exception):
                await config_manager.load_config()
        
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_reload_config(self, config_manager):
        """Test configuration reloading."""
        # Load initial config
        config1 = await config_manager.load_config()
        
        # Reload config
        config2 = await config_manager.reload_config()
        
        assert config1 is not config2  # Should be different instances
        assert config1.endpoints[0].name == config2.endpoints[0].name
    
    def test_add_reload_callback(self, config_manager):
        """Test adding reload callbacks."""
        callback_called = False
        
        def test_callback(config):
            nonlocal callback_called
            callback_called = True
        
        config_manager.add_reload_callback(test_callback)
        assert test_callback in config_manager.reload_callbacks
    
    def test_remove_reload_callback(self, config_manager):
        """Test removing reload callbacks."""
        def test_callback(config):
            pass
        
        config_manager.add_reload_callback(test_callback)
        config_manager.remove_reload_callback(test_callback)
        assert test_callback not in config_manager.reload_callbacks
    
    def test_get_config(self, config_manager):
        """Test getting current configuration."""
        assert config_manager.get_config() is None
        
        # After loading, should return config
        config_manager.config = OrchestratorConfig()
        assert config_manager.get_config() is not None
    
    def test_is_loaded(self, config_manager):
        """Test configuration loaded status."""
        assert not config_manager.is_loaded()
        
        config_manager.config = OrchestratorConfig()
        assert config_manager.is_loaded()
    
    def test_get_status(self, config_manager):
        """Test getting configuration status."""
        status = config_manager.get_status()
        
        assert "loaded" in status
        assert "version" in status
        assert "config_path" in status
        assert "endpoints_count" in status
        assert "watching" in status
    
    @pytest.mark.asyncio
    async def test_validate_config_file_valid(self, temp_config_file):
        """Test validating a valid configuration file."""
        config_manager = ConfigManager()
        is_valid, error = await config_manager.validate_config_file(temp_config_file)
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_config_file_invalid(self):
        """Test validating an invalid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            config_manager = ConfigManager()
            is_valid, error = await config_manager.validate_config_file(f.name)
            
            assert is_valid is False
            assert error is not None
        
        Path(f.name).unlink(missing_ok=True)
    
    def test_start_stop_watching(self, config_manager):
        """Test starting and stopping file watching."""
        # Start watching
        config_manager.start_watching()
        assert config_manager.observer is not None
        
        # Stop watching
        config_manager.stop_watching()
        assert config_manager.observer is None