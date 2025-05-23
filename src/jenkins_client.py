"""
Jenkins API Client for MCP Server

Handles communication with Jenkins API to extract build logs.
"""
import requests
from typing import Dict, List, Optional, Tuple, Any
import json
import time
import logging


class JenkinsClient:
    """Client for interacting with Jenkins API."""

    def __init__(self, config_manager, auth_manager):
        """
        Initialize the Jenkins API client.

        Args:
            config_manager: Configuration manager instance
            auth_manager: Authentication manager instance
        """
        self.config_manager = config_manager
        self.auth_manager = auth_manager
        self.base_url = self.config_manager.get('jenkins.url').rstrip('/')
        self.session = requests.Session()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config_manager.get('logging.level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config_manager.get('logging.file')
        )
        self.logger = logging.getLogger('jenkins_client')

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a request to the Jenkins API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.auth_manager.get_auth_headers()
        
        # Add default headers
        if 'headers' in kwargs:
            kwargs['headers'].update(headers)
        else:
            kwargs['headers'] = headers
            
        # Add JSON content type for POST/PUT requests
        if method.upper() in ('POST', 'PUT') and 'json' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            
        # Add CSRF protection if needed
        if method.upper() in ('POST', 'PUT', 'DELETE'):
            csrf_token = self._get_csrf_token()
            if csrf_token:
                kwargs['headers']['Jenkins-Crumb'] = csrf_token
                
        # Make the request with retries
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Check if we need to authenticate
                if response.status_code == 401:
                    self.logger.warning("Authentication failed, retrying...")
                    # Clear session and retry
                    self.session = requests.Session()
                    continue
                    
                # Check for other errors
                if response.status_code >= 400:
                    self.logger.error(f"API error: {response.status_code} - {response.text}")
                    
                return response
                
            except requests.RequestException as e:
                self.logger.error(f"Request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to make request after retries")

    def _get_csrf_token(self) -> Optional[str]:
        """
        Get CSRF token (crumb) for Jenkins API.

        Returns:
            CSRF token or None if not available
        """
        try:
            response = self.session.get(
                f"{self.base_url}/crumbIssuer/api/json",
                headers=self.auth_manager.get_auth_headers()
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('crumb')
        except Exception as e:
            self.logger.warning(f"Failed to get CSRF token: {e}")
        return None

    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of Jenkins jobs.

        Returns:
            List of job information dictionaries
        """
        response = self._make_request('GET', '/api/json?tree=jobs[name,url,color]')
        if response.status_code == 200:
            return response.json().get('jobs', [])
        else:
            self.logger.error(f"Failed to get jobs: {response.status_code} - {response.text}")
            return []

    def get_job_info(self, job_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific job.

        Args:
            job_name: Name of the Jenkins job

        Returns:
            Job information dictionary or None if not found
        """
        endpoint = f"/job/{job_name}/api/json"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get job info: {response.status_code} - {response.text}")
            return None

    def get_build_info(self, job_name: str, build_number: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific build.

        Args:
            job_name: Name of the Jenkins job
            build_number: Build number

        Returns:
            Build information dictionary or None if not found
        """
        endpoint = f"/job/{job_name}/{build_number}/api/json"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get build info: {response.status_code} - {response.text}")
            return None

    def get_build_log(self, job_name: str, build_number: int) -> Optional[str]:
        """
        Get console log for a specific build.

        Args:
            job_name: Name of the Jenkins job
            build_number: Build number

        Returns:
            Build log text or None if not found
        """
        endpoint = f"/job/{job_name}/{build_number}/consoleText"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.text
        else:
            self.logger.error(f"Failed to get build log: {response.status_code} - {response.text}")
            return None

    def get_last_build_log(self, job_name: str) -> Optional[str]:
        """
        Get console log for the last build of a job.

        Args:
            job_name: Name of the Jenkins job

        Returns:
            Build log text or None if not found
        """
        endpoint = f"/job/{job_name}/lastBuild/consoleText"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.text
        else:
            self.logger.error(f"Failed to get last build log: {response.status_code} - {response.text}")
            return None

    def get_build_logs(self, job_name: str, limit: int = 10) -> Dict[int, str]:
        """
        Get console logs for multiple builds of a job.

        Args:
            job_name: Name of the Jenkins job
            limit: Maximum number of builds to retrieve

        Returns:
            Dictionary mapping build numbers to log text
        """
        job_info = self.get_job_info(job_name)
        if not job_info:
            return {}
            
        builds = job_info.get('builds', [])[:limit]
        result = {}
        
        for build in builds:
            build_number = build.get('number')
            if build_number:
                log = self.get_build_log(job_name, build_number)
                if log:
                    result[build_number] = log
                    
        return result
