# Claude Code MCP Developer SDK

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code Compatible](https://img.shields.io/badge/Claude%20Code-Compatible-green.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io)

A Claude Code framework for Model Context Protocol (MCP) development, featuring specialized markdown sub-agents and MCP development templates. Primary focus on Claude Code integration with programmatic SDK requiring dependency installation.

## 🚀 Features

### Dual-Mode Architecture
- **📝 Markdown-Driven Sub-Agents**: 8 specialized agents in `.claude/agents/` for Claude Code integration
- **🔧 Programmatic SDK**: Full Python SDK with async support and official Anthropic API integration
- **🎯 Hybrid Operation**: Both systems work seamlessly together with automatic fallback

### Core Components
- ✅ **Claude Code Sub-Agents**: 8 specialized agents for MCP development assistance
- 🔒 **Security Hooks**: Input validation and dangerous command blocking
- 📝 **MCP Templates**: Working FastMCP server examples
- 🔄 **CI/CD Ready**: GitHub Actions workflows for MCP projects
- 🛠️ **Development Tools**: Validation utilities and pattern templates
- ⚠️ **SDK Components**: Programmatic API (requires `pip install -e .`)

## 📋 Requirements

- Python 3.8 or higher (3.10+ recommended)
- Claude Code (for sub-agent functionality)
- Anthropic API key (for programmatic SDK features)
- Cross-platform installation supported

## 🛠️ Installation

### Quick Start (Cross-Platform)

```bash
# Clone the repository
git clone https://github.com/gensecaihq/MCP-Developer-SubAgent.git
cd MCP-Developer-SubAgent

# Check platform compatibility  
python3 claude_code_sdk/cli_simple.py validate-setup

# Basic installation (works on all platforms)
pip install -e .        # macOS/Linux
python -m pip install -e .   # Windows

# Optional: Add authentication support
pip install -e .[auth]  # If you need JWT/crypto features
```

**📖 For detailed platform-specific instructions, see [INSTALL.md](INSTALL.md)**

### Environment Setup

**Windows (Command Prompt)**:
```batch
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Windows (PowerShell)**:
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**macOS/Linux**:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## 🎯 Usage

### 1. Markdown-Driven Sub-Agents (Claude Code)

The `.claude/agents/` directory contains 8 specialized sub-agents that work directly with Claude Code:

```
.claude/agents/
├── mcp-orchestrator.md       # Central workflow coordinator (Opus)
├── fastmcp-specialist.md     # FastMCP implementation expert (Sonnet)
├── mcp-protocol-expert.md    # Protocol specification specialist (Sonnet)
├── mcp-security-auditor.md   # Security and authentication expert (Opus)
├── mcp-performance-optimizer.md # Performance optimization specialist (Sonnet)
├── mcp-deployment-specialist.md # Deployment and infrastructure expert (Sonnet)
├── mcp-debugger.md           # Troubleshooting specialist (Sonnet)
└── context-manager.md        # Context and state management (Sonnet)
```

**Using with Claude Code:**
```bash
# Agents auto-activate based on file patterns
cd your-mcp-project
claude-code

# Request specific agents
> Use the fastmcp-specialist to implement a new tool
> Use the mcp-security-auditor to review authentication
```

### 2. Programmatic SDK (Requires Installation)

**Note**: Requires `pip install -e .` and proper dependencies

```python
from claude_code_sdk import MCPOrchestrator, FastMCPSpecialist

# Initialize orchestrator (requires ANTHROPIC_API_KEY)
orchestrator = MCPOrchestrator()
session_id = await orchestrator.create_conversation()

# Send orchestration request
message = """
Create a new MCP server with the following requirements:
- Name: my-api-server
- Tools: search, analyze, report  
- Authentication: OAuth 2.1
"""

result = await orchestrator.send_message(message, output_format="json")
print(result["content"])
```

### 3. Validation Tools

```bash
# Basic validation (works without dependencies)
python3 claude_code_sdk/cli_simple.py validate-setup
python3 claude_code_sdk/cli_simple.py status

# Advanced CLI (requires pip install -e .)
claude-mcp validate-setup
claude-mcp orchestrate --workflow new_server
```

## 🏗️ Architecture

### Directory Structure
```
MCP-Developer-SubAgent/
├── .claude/
│   ├── agents/              # Markdown sub-agents for Claude Code
│   ├── config.json          # Agent configuration
│   ├── hooks.json          # Hooks configuration
│   └── hooks/              # Hook handlers
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── claude_code_sdk/        # Programmatic SDK
│   ├── claude_integration.py
│   └── cli.py
├── examples/               # Working MCP examples
│   ├── minimal-mcp-server/
│   ├── enterprise-auth-server/
│   └── testing-framework/
├── docs/                   # Documentation
├── pyproject.toml         # Modern Python packaging
├── setup.py               # Legacy packaging support
└── requirements.txt       # Dependencies
```

### Quality Gates Pipeline

1. **Planning Gate**: Requirements, architecture, transport selection
2. **Protocol Gate**: MCP compliance, JSON-RPC validation
3. **Security Gate**: Authentication, input validation, boundaries
4. **Implementation Gate**: Code quality, type safety, patterns
5. **Testing Gate**: Coverage, compliance, integration
6. **Performance Gate**: Async patterns, optimization, benchmarks
7. **Documentation Gate**: API docs, examples, deployment guides

## 🔧 Examples

### Create MCP Server with Tools

```python
from claude_code_sdk import FastMCPSpecialist

specialist = FastMCPSpecialist()
await specialist.create_conversation()

message = """
Generate a FastMCP server with these tools:
1. search_documents - Search through documents
2. analyze_data - Analyze structured data
3. generate_report - Create formatted reports

Include proper Pydantic models and error handling.
"""

result = await specialist.send_message(message, output_format="json")
# Generated server code in result["content"]
```

### Workflow Orchestration

```python
task = {
    "type": "orchestrate_workflow",
    "workflow": "new_server",
    "requirements": {
        "name": "analytics-server",
        "tools": ["query", "aggregate", "visualize"],
        "authentication": "jwt",
        "transport": "http"
    }
}

result = await orchestrator.send_message(json.dumps(task), output_format="json")
```

## 🚦 Hooks System

Configure automation in `.claude/hooks.json`:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matchers": [{"toolType": "Write"}],
      "command": "python .claude/hooks/pre_tool_validator.py"
    },
    {
      "event": "PostToolUse",
      "matchers": [{"toolType": "Write", "fileGlob": "**/*.py"}],
      "command": "python .claude/hooks/post_tool_quality_gate.py"
    }
  ]
}
```

## 🔄 GitHub Actions Integration

Automated workflows in `.github/workflows/claude-code-mcp.yml`:

- **Pull Request Checks**: Quality gates validation, format checking
- **Issue Triggers**: Automatic MCP server generation from issues
- **Security Audits**: Automated security scanning
- **Documentation**: Auto-deploy to GitHub Pages

## 🧪 Testing

```bash
# Run tests
pytest

# Run MCP compliance tests
python examples/testing-framework/test_mcp_compliance.py \
  --server-command "python examples/minimal-mcp-server/server.py"

# Format check
black --check .

# Type checking
mypy --ignore-missing-imports .
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Best Practices](docs/best-practices.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Project Scope](scope.md) - What works, what needs setup

## 🤝 Contributing

We welcome contributions! Key areas where contributions are valuable:

### Priority Areas
- **Additional Specialist Agents**: Create new agents for specific MCP development domains
- **Enhanced Quality Gates**: Improve validation and testing frameworks
- **Performance Optimizations**: Optimize async patterns and resource usage
- **Documentation**: Improve guides, examples, and troubleshooting
- **Example Implementations**: Real-world MCP server examples

### Contributing Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing patterns
4. Test with `python3 claude_code_sdk/cli_simple.py validate-setup`
5. Submit a pull request with detailed description

### Development Setup
```bash
pip install -e .[dev]  # Install with development dependencies
pytest                 # Run tests
black .               # Format code
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[GenSecAI.org](https://gensecai.org)** - Securing the GenAI Future through advanced AI security research
- **[Anthropic](https://anthropic.com)** - Claude AI and Claude Code framework
- **MCP Protocol Community** - Model Context Protocol specification and ecosystem
- **FastMCP Contributors** - Python MCP framework development

## 🔗 Essential Links

- **[Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)** - Official Claude Code guide
- **[Model Context Protocol](https://spec.modelcontextprotocol.io)** - MCP specification
- **[Python Package Index](https://pypi.org)** - For dependency installation
- **[GitHub Issues](https://github.com/gensecaihq/MCP-Developer-SubAgent/issues)** - Report bugs or request features

---

*Claude Code framework for Model Context Protocol development with specialized sub-agents, security hooks, and MCP server templates.*