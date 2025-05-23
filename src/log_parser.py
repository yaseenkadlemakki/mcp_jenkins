"""
Log Parser for MCP Server

Processes Jenkins build logs and extracts structured information.
"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class LogParser:
    """Parser for Jenkins build logs."""

    def __init__(self, config_manager):
        """
        Initialize the log parser.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config_manager.get('logging.level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config_manager.get('logging.file')
        )
        self.logger = logging.getLogger('log_parser')
        
        # Regex patterns for log parsing
        self.timestamp_pattern = re.compile(r'(\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}(?:\.\d+)?)')
        self.started_by_pattern = re.compile(r'Started by (.+)')
        self.build_number_pattern = re.compile(r'Building in workspace (.+)')
        self.checkout_pattern = re.compile(r'Checking out (.+)')
        self.error_pattern = re.compile(r'ERROR:|Exception:|Error:|FATAL:', re.IGNORECASE)
        self.warning_pattern = re.compile(r'WARNING:|WARN:', re.IGNORECASE)
        self.success_pattern = re.compile(r'Finished: SUCCESS')
        self.failure_pattern = re.compile(r'Finished: FAILURE')
        self.unstable_pattern = re.compile(r'Finished: UNSTABLE')
        self.aborted_pattern = re.compile(r'Finished: ABORTED')

    def parse_log(self, log_text: str, job_name: str, build_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse Jenkins build log text into structured data.

        Args:
            log_text: Raw log text from Jenkins
            job_name: Name of the Jenkins job
            build_number: Build number (optional)

        Returns:
            Dictionary with structured log data
        """
        if not log_text:
            self.logger.warning(f"Empty log text for job {job_name}, build {build_number}")
            return {
                "job_name": job_name,
                "build_number": build_number,
                "status": "UNKNOWN",
                "timestamp": datetime.now().isoformat(),
                "started_by": "UNKNOWN",
                "duration": 0,
                "errors": [],
                "warnings": [],
                "stages": [],
                "log_lines": []
            }
            
        # Split log into lines
        lines = log_text.splitlines()
        
        # Extract basic information
        started_by = "UNKNOWN"
        workspace = "UNKNOWN"
        checkout = "UNKNOWN"
        errors = []
        warnings = []
        stages = []
        log_lines = []
        current_stage = None
        
        # Determine build status
        status = "UNKNOWN"
        if self.success_pattern.search(log_text):
            status = "SUCCESS"
        elif self.failure_pattern.search(log_text):
            status = "FAILURE"
        elif self.unstable_pattern.search(log_text):
            status = "UNSTABLE"
        elif self.aborted_pattern.search(log_text):
            status = "ABORTED"
            
        # Extract timestamp from first line if available
        timestamp = datetime.now().isoformat()
        for line in lines[:10]:  # Check first few lines for timestamp
            timestamp_match = self.timestamp_pattern.search(line)
            if timestamp_match:
                try:
                    # Try to parse the timestamp
                    ts = timestamp_match.group(1)
                    # Handle different date formats
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', 
                               '%m-%d-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S'):
                        try:
                            timestamp = datetime.strptime(ts, fmt).isoformat()
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp: {e}")
                break
                
        # Process each line
        for line_num, line in enumerate(lines):
            # Add to log lines with line number
            log_lines.append({"line_number": line_num + 1, "text": line})
            
            # Extract started by
            started_match = self.started_by_pattern.search(line)
            if started_match:
                started_by = started_match.group(1)
                
            # Extract workspace
            workspace_match = self.build_number_pattern.search(line)
            if workspace_match:
                workspace = workspace_match.group(1)
                
            # Extract checkout
            checkout_match = self.checkout_pattern.search(line)
            if checkout_match:
                checkout = checkout_match.group(1)
                
            # Check for errors
            if self.error_pattern.search(line):
                errors.append({"line_number": line_num + 1, "text": line})
                
            # Check for warnings
            if self.warning_pattern.search(line):
                warnings.append({"line_number": line_num + 1, "text": line})
                
            # Detect stage changes (simplified)
            if line.strip().startswith('[') and ']' in line:
                stage_name = line.split(']')[0].strip('[')
                if stage_name and stage_name != current_stage:
                    current_stage = stage_name
                    stages.append({
                        "name": current_stage,
                        "start_line": line_num + 1,
                        "end_line": None  # Will be updated later
                    })
            
            # Update end line of current stage
            if current_stage and stages:
                stages[-1]["end_line"] = line_num + 1
                
        # Calculate approximate duration based on timestamps in log
        duration = 0
        if len(log_lines) > 1:
            try:
                first_timestamp = None
                last_timestamp = None
                
                # Find first timestamp
                for line in log_lines[:100]:  # Check first 100 lines
                    timestamp_match = self.timestamp_pattern.search(line["text"])
                    if timestamp_match:
                        first_timestamp = timestamp_match.group(1)
                        break
                        
                # Find last timestamp
                for line in reversed(log_lines[:100]):  # Check last 100 lines
                    timestamp_match = self.timestamp_pattern.search(line["text"])
                    if timestamp_match:
                        last_timestamp = timestamp_match.group(1)
                        break
                        
                # Calculate duration if both timestamps found
                if first_timestamp and last_timestamp:
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', 
                               '%m-%d-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S'):
                        try:
                            start_time = datetime.strptime(first_timestamp, fmt)
                            end_time = datetime.strptime(last_timestamp, fmt)
                            duration = (end_time - start_time).total_seconds()
                            break
                        except ValueError:
                            continue
            except Exception as e:
                self.logger.warning(f"Failed to calculate duration: {e}")
                
        # Compile results
        result = {
            "job_name": job_name,
            "build_number": build_number,
            "status": status,
            "timestamp": timestamp,
            "started_by": started_by,
            "workspace": workspace,
            "checkout": checkout,
            "duration": duration,
            "errors": errors,
            "warnings": warnings,
            "stages": stages,
            "log_lines": log_lines
        }
        
        return result
