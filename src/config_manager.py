"""
Configuration Manager for MCP Server

Handles loading, validation, and access to configuration settings.
"""
import os
import yaml
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for the MCP server."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "config.yaml"
        )
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as config_file:
                    self.config = yaml.safe_load(config_file) or {}
            else:
                self.config = {}
                self._create_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration file if none exists."""
        default_config = {
            "jenkins": {
                "url": "http://localhost:8080",  # Demo URL
                "auth": {
                    "type": "token",  # or "basic"
                    "username": "",
                    "token": "",
                    "password": ""
                }
            },
            "logging": {
                "level": "INFO",
                "file": "mcp_server.log"
            },
            "output": {
                "xml_path": "output/jenkins_logs.xml",
                "pretty_print": True
            }
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write default config
        with open(self.config_path, 'w') as config_file:
            yaml.dump(default_config, config_file, default_flow_style=False)
        
        self.config = default_config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the nested dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as config_file:
                yaml.dump(self.config, config_file, default_flow_style=False)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check if Jenkins URL is set
        if not self.get('jenkins.url'):
            print("Error: Jenkins URL is not configured")
            return False
            
        # Check if authentication is properly configured
        auth_type = self.get('jenkins.auth.type')
        if auth_type == 'token':
            if not self.get('jenkins.auth.token'):
                print("Error: Jenkins API token is not configured")
                return False
        elif auth_type == 'basic':
            if not self.get('jenkins.auth.username') or not self.get('jenkins.auth.password'):
                print("Error: Jenkins username or password is not configured")
                return False
        else:
            print(f"Error: Unsupported authentication type: {auth_type}")
            return False
            
        return True
