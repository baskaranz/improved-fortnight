"""
Configuration management for the orchestrator service.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import ValidationError

from .models import OrchestratorConfig


logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for configuration file changes."""
    
    def __init__(self, config_manager: 'ConfigManager') -> None:
        self.config_manager = config_manager
        super().__init__()
    
    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        
        if event.src_path == str(self.config_manager.config_path):
            logger.info(f"Configuration file changed: {event.src_path}")
            asyncio.create_task(self.config_manager.reload_config())


class ConfigManager:
    """Manages configuration loading, validation, and reloading."""
    
    def __init__(self, config_path: str = "config/config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config: Optional[OrchestratorConfig] = None
        self.observer: Optional[Observer] = None
        self.reload_callbacks: list[Callable[[OrchestratorConfig], None]] = []
        self.version = "1.0.0"
        self.last_reload_error: Optional[str] = None
    
    async def load_config(self) -> OrchestratorConfig:
        """Load configuration from file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                # Create default configuration
                self.config = OrchestratorConfig()
                await self._save_default_config()
                return self.config
            
            logger.info(f"Loading configuration from: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            if config_data is None:
                config_data = {}
            
            self.config = OrchestratorConfig(**config_data)
            self.last_reload_error = None
            logger.info(f"Configuration loaded successfully with {len(self.config.endpoints)} endpoints")
            
            return self.config
            
        except ValidationError as e:
            error_msg = f"Configuration validation error: {e}"
            logger.error(error_msg)
            self.last_reload_error = error_msg
            raise
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            logger.error(error_msg)
            self.last_reload_error = error_msg
            raise
    
    async def reload_config(self) -> OrchestratorConfig:
        """Reload configuration and notify callbacks."""
        try:
            old_config = self.config
            new_config = await self.load_config()
            
            # Notify callbacks about config changes
            for callback in self.reload_callbacks:
                try:
                    callback(new_config)
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")
            
            logger.info("Configuration reloaded successfully")
            return new_config
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            # Keep the old configuration if reload fails
            if self.config is None:
                # If we don't have any config, create a default one
                self.config = OrchestratorConfig()
            raise
    
    def add_reload_callback(self, callback: Callable[[OrchestratorConfig], None]) -> None:
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[OrchestratorConfig], None]) -> None:
        """Remove a reload callback."""
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)
    
    def start_watching(self) -> None:
        """Start watching the configuration file for changes."""
        if self.observer is not None:
            return
        
        try:
            self.observer = Observer()
            event_handler = ConfigFileHandler(self)
            
            # Watch the directory containing the config file
            watch_path = self.config_path.parent
            if not watch_path.exists():
                watch_path.mkdir(parents=True, exist_ok=True)
            
            self.observer.schedule(event_handler, str(watch_path), recursive=False)
            self.observer.start()
            logger.info(f"Started watching configuration directory: {watch_path}")
            
        except Exception as e:
            logger.error(f"Failed to start configuration file watching: {e}")
    
    def stop_watching(self) -> None:
        """Stop watching the configuration file."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped watching configuration file")
    
    async def _save_default_config(self) -> None:
        """Save default configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "endpoints": [
                    {
                        "url": "https://httpbin.org/get",
                        "name": "httpbin_get",
                        "version": "v1",
                        "methods": ["GET"],
                        "auth_type": "none",
                        "disabled": False,
                        "health_check_path": "/get",
                        "timeout": 30
                    },
                    {
                        "url": "https://jsonplaceholder.typicode.com/posts",
                        "name": "jsonplaceholder_posts",
                        "version": "v1", 
                        "methods": ["GET", "POST"],
                        "auth_type": "none",
                        "disabled": False,
                        "timeout": 30
                    }
                ],
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "reset_timeout": 60,
                    "half_open_max_calls": 3,
                    "fallback_strategy": "error_response"
                },
                "health_check": {
                    "enabled": True,
                    "interval": 30,
                    "timeout": 10,
                    "unhealthy_threshold": 3,
                    "healthy_threshold": 2
                },
                "log_level": "INFO"
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(default_config, file, default_flow_style=False, indent=2)
                
            logger.info(f"Created default configuration file: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save default configuration: {e}")
    
    def get_config(self) -> Optional[OrchestratorConfig]:
        """Get current configuration."""
        return self.config
    
    def is_loaded(self) -> bool:
        """Check if configuration is loaded."""
        return self.config is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get configuration status information."""
        return {
            "loaded": self.is_loaded(),
            "version": self.version,
            "config_path": str(self.config_path),
            "endpoints_count": len(self.config.endpoints) if self.config else 0,
            "last_reload_error": self.last_reload_error,
            "watching": self.observer is not None and self.observer.is_alive()
        }
    
    async def validate_config_file(self, config_path: str) -> tuple[bool, Optional[str]]:
        """Validate a configuration file without loading it."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            if config_data is None:
                config_data = {}
            
            OrchestratorConfig(**config_data)
            return True, None
            
        except ValidationError as e:
            return False, f"Validation error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def __del__(self) -> None:
        """Cleanup on destruction."""
        self.stop_watching()