"""
MCP Server Core for Jenkins Log Extraction

Main module that orchestrates the workflow between components.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Tuple

from src.config_manager import ConfigManager
from src.auth_manager import AuthenticationManager
from src.jenkins_client import JenkinsClient
from src.log_parser import LogParser
from src.xml_transformer import XmlTransformer


class MCPServer:
    """Master Control Program Server for Jenkins Log Extraction."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP server.

        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.auth_manager = AuthenticationManager(self.config_manager)
        self.jenkins_client = JenkinsClient(self.config_manager, self.auth_manager)
        self.log_parser = LogParser(self.config_manager)
        self.xml_transformer = XmlTransformer(self.config_manager)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config_manager.get('logging.level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config_manager.get('logging.file')
        )
        self.logger = logging.getLogger('mcp_server')
        
    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """
        Validate server configuration.

        Returns:
            Tuple of (success, error_message)
        """
        # Validate configuration
        if not self.config_manager.validate():
            return False, "Invalid configuration"
            
        # Test authentication
        auth_success, auth_error = self.auth_manager.test_authentication()
        if not auth_success:
            return False, f"Authentication error: {auth_error}"
            
        return True, None
        
    def extract_job_logs(self, job_name: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Extract and parse logs for a specific job.

        Args:
            job_name: Name of the Jenkins job
            limit: Maximum number of builds to retrieve

        Returns:
            List of parsed log dictionaries
        """
        self.logger.info(f"Extracting logs for job: {job_name}, limit: {limit}")
        
        # Get build logs
        build_logs = self.jenkins_client.get_build_logs(job_name, limit)
        
        # Parse logs
        parsed_logs = []
        for build_number, log_text in build_logs.items():
            parsed_log = self.log_parser.parse_log(log_text, job_name, build_number)
            parsed_logs.append(parsed_log)
            
        return parsed_logs
        
    def extract_last_build_log(self, job_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse log for the last build of a job.

        Args:
            job_name: Name of the Jenkins job

        Returns:
            Parsed log dictionary or None if not found
        """
        self.logger.info(f"Extracting last build log for job: {job_name}")
        
        # Get last build log
        log_text = self.jenkins_client.get_last_build_log(job_name)
        if not log_text:
            return None
            
        # Parse log
        parsed_log = self.log_parser.parse_log(log_text, job_name)
        return parsed_log
        
    def transform_logs_to_xml(self, parsed_logs: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Transform parsed logs to XML and save to file.

        Args:
            parsed_logs: List of parsed log dictionaries
            output_path: Path to save XML file (optional)

        Returns:
            Path to saved XML file
        """
        self.logger.info(f"Transforming {len(parsed_logs)} logs to XML")
        
        # Create root element
        root = self.xml_transformer.transform_to_xml(parsed_logs[0])
        
        # Add additional logs if multiple
        if len(parsed_logs) > 1:
            # Remove the first log from root and create a builds element
            builds = ET.Element("builds")
            for parsed_log in parsed_logs:
                build_xml = self.xml_transformer.transform_to_xml(parsed_log)
                builds.append(build_xml)
            root = builds
            
        # Validate XML
        if not self.xml_transformer.validate_xml(root):
            self.logger.error("XML validation failed")
            raise ValueError("XML validation failed")
            
        # Save to file
        xml_path = self.xml_transformer.save_to_file(root, output_path)
        return xml_path
        
    def process_job(self, job_name: str, limit: int = 1, output_path: Optional[str] = None) -> str:
        """
        Process a Jenkins job: extract logs, parse, and transform to XML.

        Args:
            job_name: Name of the Jenkins job
            limit: Maximum number of builds to retrieve
            output_path: Path to save XML file (optional)

        Returns:
            Path to saved XML file
        """
        self.logger.info(f"Processing job: {job_name}")
        
        # Validate configuration
        valid, error = self.validate_configuration()
        if not valid:
            raise ValueError(f"Configuration validation failed: {error}")
            
        # Extract and parse logs
        parsed_logs = self.extract_job_logs(job_name, limit)
        if not parsed_logs:
            raise ValueError(f"No logs found for job: {job_name}")
            
        # Transform to XML and save
        xml_path = self.transform_logs_to_xml(parsed_logs, output_path)
        
        self.logger.info(f"Job processing completed: {job_name}")
        return xml_path
