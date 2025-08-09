# Getting Started with Claude Code MCP Developer SDK

## Overview

The Claude Code MCP Developer SDK provides a dual-mode architecture for developing Model Context Protocol (MCP) servers:

1. **Markdown-Driven Sub-Agents**: Work directly with Claude Code through specialized agents
2. **Programmatic SDK**: Full Python SDK for automation and integration

## Prerequisites

- Python 3.8 or higher (3.10+ recommended)
- Git
- Anthropic API key (for programmatic SDK)
- Claude Code (for sub-agent functionality)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/MCP-Developer-SubAgent.git
cd MCP-Developer-SubAgent
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install the package
pip install -e .
```

### 3. Configure Environment

```bash
# Set environment variable (required for programmatic SDK)
# Windows Command Prompt:
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"  

# macOS/Linux:
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Quick Start

### Option 1: Validate Setup (No Dependencies Required)

```bash
# Check repository status
python3 claude_code_sdk/cli_simple.py validate-setup

# View component status
python3 claude_code_sdk/cli_simple.py status
```

### Option 2: Using Markdown Sub-Agents with Claude Code

```bash
# Navigate to your MCP project
cd your-mcp-project

# Start Claude Code - agents auto-activate
claude-code

# Request specific help
> Use the mcp-orchestrator to plan a new MCP server
> Use the fastmcp-specialist to implement tools
```

### Option 2: Using the Programmatic SDK

```python
import asyncio
from claude_code_sdk import MCPOrchestrator

async def create_mcp_server():
    # Initialize orchestrator
    orchestrator = MCPOrchestrator()  # Uses ANTHROPIC_API_KEY from env
    
    # Create conversation
    session_id = await orchestrator.create_conversation()
    
    # Request server creation
    message = """
    Create a new MCP server with:
    - Name: document-processor
    - Tools: parse_pdf, extract_text, summarize
    - Authentication: none (local use)
    """
    
    result = await orchestrator.send_message(message, output_format="json")
    print(result["content"])

# Run the async function
asyncio.run(create_mcp_server())
```

### Option 3: Using the CLI

```bash
# Validate your setup
claude-mcp validate-setup

# Generate a new MCP server
claude-mcp generate-server \
  --server-name my-first-server \
  --tools '["search", "analyze"]' \
  --auth none \
  --output my_server.py

# Run quality gates on existing code
claude-mcp quality-gates \
  --gates planning,implementation \
  --context '{"files": ["my_server.py"]}'
```

## Your First MCP Server

Let's create a simple MCP server step by step:

### Step 1: Define Requirements

Create `requirements.json`:

```json
{
  "name": "weather-service",
  "description": "MCP server for weather data",
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "parameters": {
        "location": "string",
        "units": "celsius|fahrenheit"
      }
    }
  ],
  "authentication": "none",
  "transport": "stdio"
}
```

### Step 2: Generate the Server

```bash
claude-mcp orchestrate \
  --workflow new_server \
  --requirements requirements.json \
  --output weather_server.py
```

### Step 3: Review and Test

The generated server includes:
- FastMCP decorators for tools
- Pydantic models for type safety
- Error handling
- Logging setup
- Async support

### Step 4: Run the Server

```bash
python weather_server.py
```

## Working with Sub-Agents

### Available Sub-Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `mcp-orchestrator` | Opus | Workflow coordination, quality gates |
| `fastmcp-specialist` | Sonnet | FastMCP implementation, Python code |
| `mcp-protocol-expert` | Sonnet | Protocol compliance, transport layers |
| `mcp-security-auditor` | Opus | Security review, authentication |
| `mcp-performance-optimizer` | Sonnet | Performance tuning, async patterns |
| `mcp-deployment-specialist` | Sonnet | Deployment, containerization |
| `mcp-debugger` | Sonnet | Troubleshooting, error analysis |
| `context-manager` | Sonnet | State management, coordination |

### Auto-Activation Patterns

Agents automatically activate based on file patterns:

- `**/*mcp*.py` → mcp-orchestrator
- `**/fastmcp_*.py` → fastmcp-specialist
- `**/auth*.py` → mcp-security-auditor
- `**/test*.py` → mcp-debugger

## Workflow Examples

### Complete Development Workflow

```python
# 1. Planning Phase
planning_task = {
    "type": "run_quality_gates",
    "gates": ["planning"],
    "context": {
        "requirements": {...},
        "architecture": {...}
    }
}

# 2. Implementation Phase
implementation_task = {
    "type": "delegate_task",
    "specialist": "fastmcp-specialist",
    "task": {
        "action": "implement_server",
        "requirements": {...}
    }
}

# 3. Security Review
security_task = {
    "type": "delegate_task",
    "specialist": "mcp-security-auditor",
    "task": {
        "action": "audit",
        "code": "..."
    }
}

# 4. Deployment Preparation
deployment_task = {
    "type": "delegate_task",
    "specialist": "mcp-deployment-specialist",
    "task": {
        "action": "containerize",
        "server": "..."
    }
}
```

## Hooks Configuration

Enable automation with hooks in `.claude/hooks.json`:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "description": "Validate before file writes",
      "matchers": [{"toolType": "Write"}],
      "command": "python .claude/hooks/pre_tool_validator.py"
    }
  ]
}
```

## Environment Variables

Key environment variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional (for advanced usage)
# These are not required for basic functionality
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for working MCP servers
2. **Learn Best Practices**: Review [Best Practices](best-practices.md) for production tips
3. **Check Project Scope**: See [scope.md](../scope.md) for what works vs what needs setup
4. **Get Help**: See [Troubleshooting](troubleshooting.md) for common issues

## Troubleshooting

### Common Issues

**API Key Not Found**
```bash
export ANTHROPIC_API_KEY=your-key-here
# Or add to .env file
```

**Python Version Error**
```bash
# Ensure Python 3.10+
python --version
```

**Import Errors**
```bash
# Reinstall in development mode
pip install -e .
```

For more help, see the [Troubleshooting Guide](troubleshooting.md) or check [scope.md](../scope.md) for component status.