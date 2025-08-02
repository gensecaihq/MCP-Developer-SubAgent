# MCP Developer Sub-Agent

A professional-grade Claude sub-agent specialized in Model Context Protocol (MCP) development, designed to assist with building, debugging, and optimizing MCP servers and clients.

## 🚀 Overview

This repository contains a highly specialized Claude sub-agent configuration for MCP development tasks. The agent has deep expertise in:

- **MCP Protocol Specification** (v1.0.0)
- **FastMCP Framework** implementation
- **Protocol debugging** and optimization
- **Integration patterns** for various MCP clients

## 📋 Features

### Core Capabilities
- ✅ Complete understanding of MCP specification
- ✅ Expert-level FastMCP framework knowledge
- ✅ JSON-RPC 2.0 protocol implementation
- ✅ Async/await patterns and best practices
- ✅ Comprehensive error handling strategies
- ✅ Performance optimization techniques

### Specialized Skills
- 🔧 MCP server development
- 🔍 Protocol-level debugging
- 🔌 Client integration (Claude Desktop, VS Code, custom)
- 📊 Resource and tool management
- 🧪 Testing and validation strategies

## 🛠️ Usage

### With Claude Code

1. Configure Claude Code to use this sub-agent:
   ```bash
   claude-code --agent subagents/mcp-developer.md
   ```

2. Start developing your MCP project:
   ```bash
   claude-code "Create an MCP server for database operations"
   ```

### Integration Examples

```python
# Example: Using the sub-agent to create an MCP server
from fastmcp import FastMCP, Tool

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool implementation following sub-agent patterns"""
    return f"Processed: {param}"
```

## 📁 Repository Structure

```
mcp-developer-subagent/
├── README.md                 # This file
├── subagents/               # Sub-agent configurations
│   └── mcp-developer.md     # Main MCP developer sub-agent
├── examples/                # Example implementations
│   ├── basic-server.py      # Basic MCP server example
│   ├── database-tools.py    # Database integration example
│   └── debugging-guide.md   # Protocol debugging guide
└── docs/                    # Additional documentation
    ├── best-practices.md    # MCP development best practices
    └── troubleshooting.md   # Common issues and solutions
```

## 🎯 Use Cases

- **Building MCP Servers**: Create robust MCP servers with proper tool and resource management
- **Debugging Protocol Issues**: Trace and fix JSON-RPC communication problems
- **Performance Optimization**: Implement efficient async patterns and connection pooling
- **Integration Development**: Build seamless integrations with Claude Desktop and other clients
- **Testing Strategies**: Develop comprehensive test suites for MCP implementations

## 🔧 Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/gensecaihq/mcp-developer-subagent.git
   cd mcp-developer-subagent
   ```

2. Review the sub-agent configuration:
   ```bash
   cat subagents/mcp-developer.md
   ```

3. Use with Claude Code for MCP development:
   ```bash
   claude-code --agent subagents/mcp-developer.md "Help me build an MCP server"
   ```

## 📚 Resources

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas for contribution:

- Additional example implementations
- Enhanced debugging strategies
- Performance optimization patterns
- Integration templates
- Documentation improvements

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Anthropic team for Claude and the sub-agent framework
- MCP protocol developers
- FastMCP framework creators
- The MCP community

---

*Built with expertise in MCP protocol development and FastMCP framework implementation.*
