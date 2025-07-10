"""
Application configuration management for HL7 OpenSoup.

This module handles loading and saving application settings, user preferences,
and configuration data.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class AppConfig:
    """Application configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file: Optional path to configuration file. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration directory
        self.config_dir = Path.home() / ".hl7opensoup"
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration file path
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = self.config_dir / "config.yaml"
        
        # Default configuration
        self.default_config = {
            "application": {
                "theme": "default",
                "auto_save": True,
                "auto_save_interval": 300,  # seconds
                "recent_files_limit": 10,
                "startup_check_updates": True,
            },
            "ui": {
                "window_geometry": None,
                "window_state": None,
                "splitter_states": {},
                "font_family": "Consolas",
                "font_size": 10,
                "syntax_highlighting": True,
                "line_numbers": True,
                "word_wrap": False,
            },
            "hl7": {
                "default_version": "2.5",
                "validation_enabled": True,
                "auto_format": True,
                "field_separator": "|",
                "component_separator": "^",
                "repetition_separator": "~",
                "escape_character": "\\",
                "subcomponent_separator": "&",
            },
            "export": {
                "default_format": "json",
                "json_indent": 2,
                "xml_pretty_print": True,
                "csv_delimiter": ",",
                "include_metadata": True,
            },
            "database": {
                "enabled": False,
                "connection_string": "",
                "database_name": "hl7_messages",
                "collection_name": "messages",
                "auto_connect": False,
            },
            "recent_files": [],
            "custom_schemas": [],
        }
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.suffix.lower() == '.yaml':
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_config = self._merge_configs(self.default_config, config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return merged_config
            else:
                self.logger.info("No configuration file found, using defaults")
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'ui.font_size')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'ui.font_size')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add
        """
        recent_files = self.get('recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Limit the list size
        limit = self.get('application.recent_files_limit', 10)
        recent_files = recent_files[:limit]
        
        self.set('recent_files', recent_files)
    
    def get_recent_files(self) -> list:
        """Get list of recent files, filtering out non-existent files.
        
        Returns:
            List of existing recent file paths
        """
        recent_files = self.get('recent_files', [])
        existing_files = [f for f in recent_files if Path(f).exists()]
        
        # Update the list if files were removed
        if len(existing_files) != len(recent_files):
            self.set('recent_files', existing_files)
        
        return existing_files
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user configuration with defaults.
        
        Args:
            default: Default configuration dictionary
            user: User configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
