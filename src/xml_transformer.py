"""
XML Transformer for MCP Server

Transforms parsed Jenkins build logs into XML format.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from typing import Dict, Any, Optional
import logging


class XmlTransformer:
    """Transforms parsed log data to XML format."""

    def __init__(self, config_manager):
        """
        Initialize the XML transformer.

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
        self.logger = logging.getLogger('xml_transformer')

    def transform_to_xml(self, parsed_log: Dict[str, Any]) -> ET.Element:
        """
        Transform parsed log data to XML Element.

        Args:
            parsed_log: Dictionary with parsed log data

        Returns:
            XML Element representing the log data
        """
        # Create root element
        root = ET.Element("jenkins_build_log")
        
        # Add build information
        build_info = ET.SubElement(root, "build_info")
        ET.SubElement(build_info, "job_name").text = str(parsed_log.get("job_name", ""))
        ET.SubElement(build_info, "build_number").text = str(parsed_log.get("build_number", ""))
        ET.SubElement(build_info, "status").text = parsed_log.get("status", "UNKNOWN")
        ET.SubElement(build_info, "timestamp").text = parsed_log.get("timestamp", "")
        ET.SubElement(build_info, "started_by").text = parsed_log.get("started_by", "")
        ET.SubElement(build_info, "workspace").text = parsed_log.get("workspace", "")
        ET.SubElement(build_info, "checkout").text = parsed_log.get("checkout", "")
        ET.SubElement(build_info, "duration").text = str(parsed_log.get("duration", 0))
        
        # Add errors
        errors = ET.SubElement(root, "errors")
        for error in parsed_log.get("errors", []):
            error_elem = ET.SubElement(errors, "error")
            ET.SubElement(error_elem, "line_number").text = str(error.get("line_number", 0))
            ET.SubElement(error_elem, "text").text = error.get("text", "")
        
        # Add warnings
        warnings = ET.SubElement(root, "warnings")
        for warning in parsed_log.get("warnings", []):
            warning_elem = ET.SubElement(warnings, "warning")
            ET.SubElement(warning_elem, "line_number").text = str(warning.get("line_number", 0))
            ET.SubElement(warning_elem, "text").text = warning.get("text", "")
        
        # Add stages
        stages = ET.SubElement(root, "stages")
        for stage in parsed_log.get("stages", []):
            stage_elem = ET.SubElement(stages, "stage")
            ET.SubElement(stage_elem, "name").text = stage.get("name", "")
            ET.SubElement(stage_elem, "start_line").text = str(stage.get("start_line", 0))
            ET.SubElement(stage_elem, "end_line").text = str(stage.get("end_line", 0))
        
        # Add log lines
        log_lines = ET.SubElement(root, "log_lines")
        for line in parsed_log.get("log_lines", []):
            line_elem = ET.SubElement(log_lines, "line")
            ET.SubElement(line_elem, "number").text = str(line.get("line_number", 0))
            ET.SubElement(line_elem, "text").text = line.get("text", "")
        
        return root

    def save_to_file(self, xml_element: ET.Element, file_path: Optional[str] = None) -> str:
        """
        Save XML to file with pretty formatting.

        Args:
            xml_element: XML Element to save
            file_path: Path to save XML file (optional)

        Returns:
            Path to saved XML file
        """
        # Use configured path if not specified
        if not file_path:
            file_path = self.config_manager.get('output.xml_path', 'output/jenkins_logs.xml')
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert to string with pretty formatting
        rough_string = ET.tostring(xml_element, 'utf-8')
        pretty_print = self.config_manager.get('output.pretty_print', True)
        
        if pretty_print:
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Remove extra whitespace around text nodes
            pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
        else:
            with open(file_path, 'wb') as f:
                f.write(rough_string)
                
        self.logger.info(f"XML saved to {file_path}")
        return file_path

    def validate_xml(self, xml_element: ET.Element) -> bool:
        """
        Validate XML structure.

        Args:
            xml_element: XML Element to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation by converting to string and parsing back
            xml_string = ET.tostring(xml_element, 'utf-8')
            ET.fromstring(xml_string)
            return True
        except Exception as e:
            self.logger.error(f"XML validation failed: {e}")
            return False
