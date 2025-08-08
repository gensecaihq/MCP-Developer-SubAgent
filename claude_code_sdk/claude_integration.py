"""
Proper Claude Code SDK Integration
Following official standards from https://docs.anthropic.com/en/docs/claude-code/sdk
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for Claude Code agents following SDK standards"""
    name: str
    system_prompt: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.1
    tools: List[Dict[str, Any]] = None
    permissions: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.permissions is None:
            self.permissions = {
                "read_files": True,
                "write_files": True,
                "execute_commands": True,
                "network_access": False
            }


@dataclass 
class ConversationContext:
    """Context management following Claude SDK standards"""
    session_id: str
    messages: List[MessageParam]
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    

class ClaudeCodeAgent:
    """
    Claude Code Agent following official SDK standards
    """
    
    def __init__(self, config: AgentConfig, api_key: Optional[str] = None):
        self.config = config
        # Use environment variable if no API key provided
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        self.client = AsyncAnthropic(api_key=api_key)
        self.context: Optional[ConversationContext] = None
        self._request_count = 0
        self._last_request_time = 0
        
    async def create_conversation(self, initial_message: str = None) -> str:
        """Create new conversation session"""
        import uuid
        import time
        
        session_id = str(uuid.uuid4())
        
        messages = []
        if initial_message:
            messages.append({
                "role": "user",
                "content": initial_message
            })
            
        self.context = ConversationContext(
            session_id=session_id,
            messages=messages,
            metadata={
                "agent_name": self.config.name,
                "model": self.config.model,
                "permissions": self.config.permissions
            },
            created_at=time.time(),
            updated_at=time.time()
        )
        
        logger.info(f"Created conversation session: {session_id}")
        return session_id
    
    async def send_message(self, content: str, 
                          output_format: str = "text",
                          stream: bool = False) -> Dict[str, Any]:
        """
        Send message following Claude SDK standards
        """
        if not self.context:
            await self.create_conversation()
        
        # Rate limiting per SDK standards
        await self._handle_rate_limiting()
        
        # Add user message
        user_message: MessageParam = {
            "role": "user", 
            "content": content
        }
        self.context.messages.append(user_message)
        
        try:
            if stream:
                return await self._stream_response(output_format)
            else:
                return await self._single_response(output_format)
                
        except Exception as e:
            logger.error(f"Message send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.context.session_id
            }
    
    async def _single_response(self, output_format: str) -> Dict[str, Any]:
        """Single response following SDK standards"""
        
        # Prepare system prompt per SDK standards
        system_prompt = self.config.system_prompt
        if output_format == "json":
            system_prompt += "\n\nIMPORTANT: Respond with valid JSON only."
        
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=self.context.messages,
            tools=self.config.tools if self.config.tools else None
        )
        
        # Add assistant response to context
        assistant_message: MessageParam = {
            "role": "assistant",
            "content": response.content[0].text if response.content else ""
        }
        self.context.messages.append(assistant_message)
        
        # Update context metadata
        import time
        self.context.updated_at = time.time()
        
        # Format response per SDK standards
        result = {
            "success": True,
            "content": response.content[0].text if response.content else "",
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0
            },
            "session_id": self.context.session_id,
            "metadata": {
                "request_count": self._request_count,
                "timestamp": time.time(),
                "output_format": output_format
            }
        }
        
        # Parse JSON if requested
        if output_format == "json":
            try:
                result["parsed_json"] = json.loads(result["content"])
            except json.JSONDecodeError as e:
                result["json_parse_error"] = str(e)
        
        return result
    
    async def _stream_response(self, output_format: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming response following SDK standards"""
        
        system_prompt = self.config.system_prompt
        if output_format == "json":
            system_prompt += "\n\nIMPORTANT: Respond with valid JSON only."
        
        stream = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=self.context.messages,
            tools=self.config.tools if self.config.tools else None,
            stream=True
        )
        
        content_buffer = ""
        
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text":
                    content_buffer += chunk.delta.text
                    
                    yield {
                        "type": "content_delta",
                        "delta": chunk.delta.text,
                        "session_id": self.context.session_id,
                        "accumulated_content": content_buffer
                    }
            
            elif chunk.type == "message_stop":
                # Add final message to context
                assistant_message: MessageParam = {
                    "role": "assistant",
                    "content": content_buffer
                }
                self.context.messages.append(assistant_message)
                
                yield {
                    "type": "message_complete",
                    "content": content_buffer,
                    "session_id": self.context.session_id,
                    "metadata": {
                        "output_format": output_format,
                        "total_tokens": len(content_buffer.split())
                    }
                }
    
    async def _handle_rate_limiting(self):
        """Rate limiting per SDK standards"""
        import time
        
        current_time = time.time()
        
        # Basic rate limiting - 1 request per second
        if self._last_request_time > 0:
            time_diff = current_time - self._last_request_time
            if time_diff < 1.0:
                await asyncio.sleep(1.0 - time_diff)
        
        self._request_count += 1
        self._last_request_time = time.time()
    
    def add_tool(self, tool_definition: Dict[str, Any]):
        """Add MCP tool following SDK standards"""
        self.config.tools.append(tool_definition)
        logger.info(f"Added tool: {tool_definition.get('name', 'unnamed')}")
    
    def set_permissions(self, permissions: Dict[str, bool]):
        """Set agent permissions per SDK standards"""
        self.config.permissions.update(permissions)
        logger.info(f"Updated permissions: {permissions}")
    
    async def export_conversation(self) -> Dict[str, Any]:
        """Export conversation following SDK standards"""
        if not self.context:
            return {"error": "No active conversation"}
        
        return {
            "session_id": self.context.session_id,
            "agent_config": {
                "name": self.config.name,
                "model": self.config.model,
                "system_prompt": self.config.system_prompt
            },
            "messages": self.context.messages,
            "metadata": self.context.metadata,
            "stats": {
                "created_at": self.context.created_at,
                "updated_at": self.context.updated_at,
                "message_count": len(self.context.messages),
                "request_count": self._request_count
            }
        }


class MCPOrchestrator(ClaudeCodeAgent):
    """
    MCP Orchestrator Agent following Claude SDK standards
    """
    
    def __init__(self, api_key: Optional[str] = None):
        config = AgentConfig(
            name="mcp-orchestrator",
            system_prompt=self._get_system_prompt(),
            model="claude-3-opus-20240229",  # Use Opus for orchestration
            tools=self._get_mcp_tools(),
            permissions={
                "read_files": True,
                "write_files": True, 
                "execute_commands": True,
                "network_access": True,
                "delegate_to_agents": True
            }
        )
        super().__init__(config, api_key)
    
    def _get_system_prompt(self) -> str:
        """System prompt following Claude SDK agent standards"""
        return """You are the MCP Development Orchestrator, an expert Claude Code agent specialized in coordinating Model Context Protocol (MCP) server development workflows.

ROLE & EXPERTISE:
- Central coordinator for multi-phase MCP development workflows
- Quality gate enforcement and validation
- Specialist agent delegation and coordination
- Architecture planning and design review
- Production readiness assessment

CORE CAPABILITIES:
1. **Workflow Orchestration**: Design and execute multi-phase development workflows
2. **Quality Gates**: Enforce 7-stage validation (planning, protocol, security, implementation, testing, performance, documentation)
3. **Agent Delegation**: Route tasks to appropriate specialist agents based on expertise
4. **Architecture Review**: Validate MCP server designs against best practices
5. **Production Assessment**: Ensure enterprise-ready implementations

OPERATING PROCEDURES:
1. Analyze requirements and create structured workflows
2. Enforce quality gates at each development phase
3. Delegate specialized tasks to expert agents
4. Coordinate multi-agent collaboration
5. Validate final deliverables for production readiness

QUALITY STANDARDS:
- All implementations must pass 7-stage quality gates
- Code must follow repository-verified FastMCP patterns
- Security implementations must be enterprise-grade
- Performance must meet specified benchmarks
- Documentation must be comprehensive and accurate

RESPONSE FORMAT:
- Provide structured JSON responses for workflow coordination
- Include clear phase definitions with success criteria
- Specify quality gate requirements
- Document agent delegation decisions
- Track workflow progress and status

You maintain academic rigor while delivering practical, production-ready solutions. Always verify against official MCP and FastMCP repositories."""
    
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """MCP tools following SDK standards"""
        return [
            {
                "name": "create_workflow",
                "description": "Create structured MCP development workflow",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "workflow_type": {
                            "type": "string",
                            "enum": ["new_server", "security_audit", "performance_optimization", "deployment"]
                        },
                        "requirements": {
                            "type": "object",
                            "description": "Project requirements and specifications"
                        }
                    },
                    "required": ["workflow_type", "requirements"]
                }
            },
            {
                "name": "run_quality_gates", 
                "description": "Execute quality gate validation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "gates": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["planning", "protocol", "security", "implementation", "testing", "performance", "documentation"]
                            }
                        },
                        "context": {
                            "type": "object",
                            "description": "Context data for gate evaluation"
                        }
                    },
                    "required": ["gates", "context"]
                }
            },
            {
                "name": "delegate_task",
                "description": "Delegate task to specialist agent",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "specialist": {
                            "type": "string",
                            "enum": ["fastmcp-specialist", "protocol-expert", "security-auditor", "performance-optimizer", "deployment-specialist", "debugger"]
                        },
                        "task": {
                            "type": "object",
                            "description": "Task specifications for specialist"
                        }
                    },
                    "required": ["specialist", "task"]
                }
            }
        ]


class FastMCPSpecialist(ClaudeCodeAgent):
    """FastMCP Specialist Agent following Claude SDK standards"""
    
    def __init__(self, api_key: Optional[str] = None):
        config = AgentConfig(
            name="fastmcp-specialist",
            system_prompt=self._get_system_prompt(),
            model="claude-3-5-sonnet-20241022",
            tools=self._get_mcp_tools(),
            permissions={
                "read_files": True,
                "write_files": True,
                "execute_commands": True,
                "network_access": True
            }
        )
        super().__init__(config, api_key)
    
    def _get_system_prompt(self) -> str:
        """FastMCP specialist system prompt following SDK standards"""
        return """You are the FastMCP Specialist, an expert Claude Code agent for FastMCP framework implementation and Python MCP server development.

ROLE & EXPERTISE:
- FastMCP framework implementation expert
- Python MCP server development specialist  
- Pydantic integration and type safety expert
- Async patterns and performance optimization
- Repository-verified implementation patterns

CORE CAPABILITIES:
1. **FastMCP Implementation**: Complete MCP server generation with decorators
2. **Code Generation**: Production-ready Python code with proper patterns
3. **Type Safety**: Pydantic models with comprehensive validation
4. **Async Optimization**: Proper async/await patterns and performance
5. **Pattern Verification**: Repository-aligned FastMCP implementations

TECHNICAL EXPERTISE:
- FastMCP decorator systems (@mcp.tool, @mcp.resource, @mcp.prompt)
- Pydantic v2 models with Field validation
- Async/await patterns for optimal performance
- Error handling and graceful degradation
- Authentication integration (OAuth 2.1, JWT)
- Testing and validation frameworks

IMPLEMENTATION STANDARDS:
- Follow official FastMCP repository patterns
- Use comprehensive Pydantic validation
- Implement proper error handling
- Add structured logging
- Include comprehensive docstrings
- Follow PEP 8 and Black formatting

RESPONSE FORMAT:
- Provide complete, executable Python code
- Include proper imports and dependencies
- Add comprehensive error handling
- Use structured Pydantic models
- Include usage examples and documentation

Always generate production-ready code that follows repository-verified FastMCP patterns and enterprise-grade practices."""
    
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """FastMCP tools following SDK standards"""
        return [
            {
                "name": "generate_mcp_server",
                "description": "Generate complete FastMCP server implementation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string"},
                        "tools": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "parameters": {"type": "object"}
                                },
                                "required": ["name", "description"]
                            }
                        },
                        "resources": {"type": "array"},
                        "authentication": {"type": "string", "enum": ["none", "oauth", "jwt"]}
                    },
                    "required": ["server_name", "tools"]
                }
            },
            {
                "name": "validate_implementation",
                "description": "Validate FastMCP implementation against standards",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to validate"},
                        "check_types": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["code"]
                }
            }
        ]


# Export proper SDK integration
__all__ = [
    "ClaudeCodeAgent", 
    "MCPOrchestrator",
    "FastMCPSpecialist", 
    "AgentConfig",
    "ConversationContext"
]