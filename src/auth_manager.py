"""
Authentication Module for MCP Server

Handles authentication with Jenkins API.
"""
import base64
from typing import Dict, Optional, Tuple


class AuthenticationManager:
    """Manages authentication for Jenkins API access."""

    def __init__(self, config_manager):
        """
        Initialize the authentication manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for Jenkins API requests.

        Returns:
            Dictionary of authentication headers
        """
        auth_type = self.config_manager.get('jenkins.auth.type')
        
        if auth_type == 'token':
            return self._get_token_auth_headers()
        elif auth_type == 'basic':
            return self._get_basic_auth_headers()
        else:
            raise ValueError(f"Unsupported authentication type: {auth_type}")

    def _get_token_auth_headers(self) -> Dict[str, str]:
        """
        Get token-based authentication headers.

        Returns:
            Dictionary with token authentication headers
        """
        username = self.config_manager.get('jenkins.auth.username', '')
        token = self.config_manager.get('jenkins.auth.token', '')
        
        if not token:
            raise ValueError("Jenkins API token is not configured")
            
        # If username is provided, use username:token format
        if username:
            auth_str = f"{username}:{token}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        # Otherwise, use token directly
        else:
            return {"Authorization": f"Bearer {token}"}

    def _get_basic_auth_headers(self) -> Dict[str, str]:
        """
        Get basic authentication headers.

        Returns:
            Dictionary with basic authentication headers
        """
        username = self.config_manager.get('jenkins.auth.username')
        password = self.config_manager.get('jenkins.auth.password')
        
        if not username or not password:
            raise ValueError("Jenkins username or password is not configured")
            
        auth_str = f"{username}:{password}"
        encoded = base64.b64encode(auth_str.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def test_authentication(self) -> Tuple[bool, Optional[str]]:
        """
        Test authentication with Jenkins.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # This method just prepares headers, doesn't actually test them
            self.get_auth_headers()
            return True, None
        except ValueError as e:
            return False, str(e)
