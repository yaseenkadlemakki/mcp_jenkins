"""
Command Line Interface for MCP Server

Provides a command-line interface for the MCP server.
"""
import argparse
import os
import sys
import logging
from src.mcp_server import MCPServer


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='MCP Server for Jenkins Log Extraction',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add arguments
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')
    )
    parser.add_argument(
        '--job', '-j',
        help='Jenkins job name',
        required=True
    )
    parser.add_argument(
        '--limit', '-l',
        help='Maximum number of builds to retrieve',
        type=int,
        default=1
    )
    parser.add_argument(
        '--output', '-o',
        help='Path to save XML output',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'jenkins_logs.xml')
    )
    parser.add_argument(
        '--verbose', '-v',
        help='Enable verbose logging',
        action='store_true'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('mcp_cli')
    
    try:
        # Initialize MCP server
        logger.info(f"Initializing MCP server with config: {args.config}")
        server = MCPServer(args.config)
        
        # Process job
        logger.info(f"Processing job: {args.job}, limit: {args.limit}")
        xml_path = server.process_job(args.job, args.limit, args.output)
        
        logger.info(f"XML output saved to: {xml_path}")
        print(f"XML output saved to: {xml_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
