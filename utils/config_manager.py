#!/usr/bin/env python3
"""
Unified configuration management for ClAP
Centralizes all configuration loading and provides consistent access patterns
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from functools import lru_cache

# Base paths
CLAP_ROOT = Path(__file__).parent.parent
HOME_DIR = Path.home()

# Configuration file paths
CONFIG_PATHS = {
    'infrastructure': CLAP_ROOT / 'config' / 'claude_infrastructure_config.txt',
    'notification': CLAP_ROOT / 'config' / 'notification_config.json',
    'channel_state': CLAP_ROOT / 'discord' / 'channel_state.json',
    'claude_config': HOME_DIR / '.config' / 'Claude' / '.claude.json',
    'session_config': CLAP_ROOT / 'config' / 'session_config.json',
    'services': CLAP_ROOT / 'config' / 'services_config.json'
}

# Fallback paths for backward compatibility
FALLBACK_PATHS = {
    'infrastructure': [
        HOME_DIR / 'claude-autonomy-platform' / 'claude_infrastructure_config.txt',
        CLAP_ROOT / 'claude_infrastructure_config.txt'
    ]
}

class ConfigManager:
    """Singleton configuration manager for ClAP"""
    _instance = None
    _cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the configuration manager"""
        self.logger = logging.getLogger('config_manager')
    
    @lru_cache(maxsize=32)
    def get_config_path(self, config_name: str) -> Optional[Path]:
        """
        Get the path to a configuration file, checking fallbacks if needed
        
        Args:
            config_name: Name of the configuration (e.g., 'infrastructure', 'notification')
        
        Returns:
            Path to the configuration file if found, None otherwise
        """
        # Check primary path
        if config_name in CONFIG_PATHS:
            primary_path = CONFIG_PATHS[config_name]
            if primary_path.exists():
                return primary_path
        
        # Check fallback paths
        if config_name in FALLBACK_PATHS:
            for fallback_path in FALLBACK_PATHS[config_name]:
                if fallback_path.exists():
                    self.logger.info(f"Using fallback path for {config_name}: {fallback_path}")
                    return fallback_path
        
        return None
    
    def load_json_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load a JSON configuration file
        
        Args:
            config_name: Name of the configuration
        
        Returns:
            Dictionary containing the configuration
        """
        # Check cache first
        cache_key = f"json_{config_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.get_config_path(config_name)
        if not config_path:
            self.logger.warning(f"Configuration file not found: {config_name}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self._cache[cache_key] = config
            return config
        except Exception as e:
            self.logger.error(f"Error loading JSON config {config_name}: {e}")
            return {}
    
    def load_text_config(self, config_name: str) -> Dict[str, str]:
        """
        Load a text configuration file (key=value format)
        
        Args:
            config_name: Name of the configuration
        
        Returns:
            Dictionary containing the configuration
        """
        # Check cache first
        cache_key = f"text_{config_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.get_config_path(config_name)
        if not config_path:
            self.logger.warning(f"Configuration file not found: {config_name}")
            return {}
        
        config = {}
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            self._cache[cache_key] = config
            return config
        except Exception as e:
            self.logger.error(f"Error loading text config {config_name}: {e}")
            return {}
    
    def get_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        Get a specific value from a configuration file
        
        Args:
            config_name: Name of the configuration
            key: Key to retrieve
            default: Default value if key not found
        
        Returns:
            The configuration value or default
        """
        config_path = self.get_config_path(config_name)
        if not config_path:
            return default
        
        # Determine config type by extension
        if config_path.suffix == '.json':
            config = self.load_json_config(config_name)
            return config.get(key, default)
        else:
            config = self.load_text_config(config_name)
            return config.get(key, default)
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._cache.clear()
        self.get_config_path.cache_clear()
    
    def reload_config(self, config_name: str):
        """
        Force reload a specific configuration
        
        Args:
            config_name: Name of the configuration to reload
        """
        # Remove from cache
        json_key = f"json_{config_name}"
        text_key = f"text_{config_name}"
        self._cache.pop(json_key, None)
        self._cache.pop(text_key, None)
        
        # Clear path cache for this config
        self.get_config_path.cache_clear()

# Convenience functions for common configurations
def get_infrastructure_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a value from the infrastructure configuration"""
    manager = ConfigManager()
    return manager.get_value('infrastructure', key, default)

def get_discord_token() -> Optional[str]:
    """Get the Discord bot token"""
    return get_infrastructure_value('DISCORD_BOT_TOKEN')

def get_notification_config() -> Dict[str, Any]:
    """Get the notification configuration"""
    manager = ConfigManager()
    return manager.load_json_config('notification')

def get_channel_state() -> Dict[str, Any]:
    """Get the Discord channel state"""
    manager = ConfigManager()
    return manager.load_json_config('channel_state')

def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a specific service"""
    manager = ConfigManager()
    services = manager.load_json_config('services')
    return services.get(service_name, {})