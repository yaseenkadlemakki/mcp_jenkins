# MCP Server for Jenkins Log Extraction - User Guide

## Overview
The Master Control Program (MCP) server is designed to extract build logs from Jenkins and transform them into a meaningful XML format. This guide provides instructions on how to set up and use the MCP server.

## Features
- Extract build logs from Jenkins via REST API
- Support for authenticated access to Jenkins
- Configurable Jenkins URL (works with both demo and real instances)
- Parsing of build logs to extract meaningful information
- Transformation of parsed logs into structured XML format
- Command-line interface for easy operation

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Dependencies
The MCP server requires the following Python packages:
- requests
- pyyaml
- lxml

You can install these dependencies using pip:

```bash
pip install requests pyyaml lxml
```

## Configuration
The MCP server uses a YAML configuration file located at `config/config.yaml`. You can customize this file to match your Jenkins environment:

```yaml
jenkins:
  url: "http://your-jenkins-server:8080"  # Your Jenkins URL
  auth:
    type: "token"  # or "basic"
    username: "your-username"  # Required for both token and basic auth
    token: "your-api-token"    # Required for token auth
    password: "your-password"  # Required for basic auth

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "mcp_server.log"

output:
  xml_path: "output/jenkins_logs.xml"
  pretty_print: true
```

### Authentication
The MCP server supports two authentication methods:

1. **Token Authentication** (Recommended)
   - Set `auth.type` to `"token"`
   - Provide your Jenkins username in `auth.username`
   - Provide your Jenkins API token in `auth.token`

2. **Basic Authentication**
   - Set `auth.type` to `"basic"`
   - Provide your Jenkins username in `auth.username`
   - Provide your Jenkins password in `auth.password`

To generate a Jenkins API token:
1. Log in to your Jenkins instance
2. Click on your username in the top right corner
3. Click on "Configure" in the left sidebar
4. Click on "Add new Token" in the API Token section
5. Give your token a name and click "Generate"
6. Copy the generated token and use it in your configuration

## Usage

### Command Line Interface
The MCP server provides a command-line interface for extracting logs:

```bash
python cli.py --job JOB_NAME [--limit LIMIT] [--output OUTPUT_PATH] [--config CONFIG_PATH] [--verbose]
```

Arguments:
- `--job`, `-j`: Jenkins job name (required)
- `--limit`, `-l`: Maximum number of builds to retrieve (default: 1)
- `--output`, `-o`: Path to save XML output (default: output/jenkins_logs.xml)
- `--config`, `-c`: Path to configuration file (default: config/config.yaml)
- `--verbose`, `-v`: Enable verbose logging

Example:
```bash
python cli.py --job my-jenkins-job --limit 5 --output my_logs.xml
```

### Using as a Library
You can also use the MCP server as a library in your Python code:

```python
from src.mcp_server import MCPServer

# Initialize MCP server with custom config
server = MCPServer('path/to/config.yaml')

# Process a job and get XML output path
xml_path = server.process_job('my-jenkins-job', limit=5, output_path='my_logs.xml')

print(f"XML output saved to: {xml_path}")
```

## XML Output Format
The MCP server generates XML output with the following structure:

```xml
<?xml version="1.0" ?>
<jenkins_build_log>
  <build_info>
    <job_name>my-jenkins-job</job_name>
    <build_number>123</build_number>
    <status>SUCCESS</status>
    <timestamp>2025-05-23T12:34:56</timestamp>
    <started_by>user</started_by>
    <workspace>/var/lib/jenkins/workspace/my-jenkins-job</workspace>
    <checkout>refs/remotes/origin/main</checkout>
    <duration>120</duration>
  </build_info>
  <errors>
    <error>
      <line_number>42</line_number>
      <text>ERROR: Build failed due to compilation error</text>
    </error>
  </errors>
  <warnings>
    <warning>
      <line_number>21</line_number>
      <text>WARNING: Deprecated API usage detected</text>
    </warning>
  </warnings>
  <stages>
    <stage>
      <name>Build</name>
      <start_line>10</start_line>
      <end_line>50</end_line>
    </stage>
    <stage>
      <name>Test</name>
      <start_line>51</start_line>
      <end_line>100</end_line>
    </stage>
  </stages>
  <log_lines>
    <line>
      <number>1</number>
      <text>Started by user</text>
    </line>
    <!-- Additional log lines -->
  </log_lines>
</jenkins_build_log>
```

## Troubleshooting

### Common Issues

1. **Authentication Failure**
   - Verify your Jenkins URL is correct
   - Check that your username and token/password are correct
   - Ensure your user has appropriate permissions in Jenkins

2. **Job Not Found**
   - Verify the job name is correct and exists in Jenkins
   - Check that your user has access to the specified job

3. **XML Output Issues**
   - Ensure the output directory exists and is writable
   - Check the log file for detailed error messages

### Logging
The MCP server logs detailed information to the file specified in the configuration. You can set the logging level to DEBUG for more detailed information:

```yaml
logging:
  level: "DEBUG"
  file: "mcp_server.log"
```

## Architecture
The MCP server follows a modular architecture with the following components:

1. **Configuration Manager**: Handles configuration loading and validation
2. **Authentication Module**: Manages Jenkins authentication
3. **Jenkins API Client**: Communicates with Jenkins REST API
4. **Log Parser**: Processes raw Jenkins build logs
5. **XML Transformer**: Converts parsed log data to XML format
6. **MCP Core Server**: Orchestrates the workflow between components
7. **CLI Interface**: Provides command-line interface

## Extending the MCP Server
The modular architecture makes it easy to extend the MCP server:

- Add support for additional Jenkins log types
- Implement alternative output formats (JSON, CSV)
- Add integration with monitoring systems
- Implement real-time log streaming

## License
This software is provided as-is with no warranty. Use at your own risk.
