"""
Claude Code SDK Integration for MCP Development
Following official standards from https://docs.anthropic.com/en/docs/claude-code/sdk
"""

from .claude_integration import (
    ClaudeCodeAgent,
    MCPOrchestrator, 
    FastMCPSpecialist,
    AgentConfig,
    ConversationContext
)

__version__ = "1.0.0"
__all__ = [
    "ClaudeCodeAgent",
    "MCPOrchestrator", 
    "FastMCPSpecialist",
    "AgentConfig", 
    "ConversationContext"
]