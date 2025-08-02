# MCP Developer Agent

This is the project-level configuration for the MCP Developer subagent, specialized for Model Context Protocol development with Claude Code.

## Agent Configuration

**Name**: `mcp-enterprise-developer`
**Version**: `2.0.0`
**Specialization**: MCP server development with FastMCP and MCP protocol implementation

## MCP Development Capabilities

- Expert knowledge of MCP protocol specification and implementation
- FastMCP framework patterns and best practices
- Structured output design with Pydantic integration
- MCP client integration and compatibility
- Production deployment patterns for MCP servers

## Usage with Claude Code

```bash
# Use this agent for MCP development tasks
claude-code --agent .claude/agents/mcp-enterprise-developer.md "Help me build a FastMCP server"

# Or activate interactively in your MCP project
claude-code
> /agent mcp-enterprise-developer
```

## MCP Project Integration

This agent is specifically designed for:
- MCP server development projects using FastMCP
- Protocol implementation and compliance
- Client integration with Claude Desktop and other MCP clients
- Production deployment of MCP servers

## Development Tools

This agent provides assistance with:
- FastMCP server code generation and patterns
- MCP protocol implementation guidance
- Tool, resource, and prompt development
- Client integration testing and validation
- Production deployment strategies

---

*This configuration enables focused MCP development with FastMCP framework and MCP protocol expertise.*