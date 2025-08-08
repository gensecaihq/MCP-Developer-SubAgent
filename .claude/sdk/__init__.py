"""
Claude Code SDK Integration Layer
Provides programmatic control over multi-agent orchestration
"""

from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from pathlib import Path

from .base_agent import BaseAgent, AgentConfig
from .registry import AgentRegistry
from .communication import MessageBus
from .context_manager import ContextManager

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


class ClaudeSDK:
    """Core SDK wrapper for Claude Code integration"""
    
    def __init__(self, config_path: str = ".claude/config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.context_manager = ContextManager()
        self._initialized = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    async def initialize(self) -> None:
        """Initialize the SDK and all components"""
        if self._initialized:
            return
            
        logger.info("Initializing Claude SDK...")
        
        # Initialize components
        await self.message_bus.initialize()
        await self.context_manager.initialize()
        
        # Auto-discover and register agents
        await self._register_agents()
        
        self._initialized = True
        logger.info("Claude SDK initialized successfully")
    
    async def _register_agents(self) -> None:
        """Register agents from configuration"""
        agents_config = self.config.get("agents", {})
        
        for agent_name, agent_info in agents_config.items():
            try:
                # Try to load programmatic agent first
                try:
                    agent_module = f"claude.agents.{agent_name.replace('-', '_')}"
                    module = __import__(agent_module, fromlist=[agent_name])
                    agent_class = getattr(module, self._get_class_name(agent_name))
                    
                    config = AgentConfig(
                        name=agent_name,
                        model=agent_info.get("model", "sonnet"),
                        description=agent_info.get("description", ""),
                        capabilities=agent_info.get("preferred_for", []),
                        auto_activate_patterns=agent_info.get("auto_activate_patterns", [])
                    )
                    
                    self.registry.register(agent_name, agent_class, config)
                    logger.info(f"Registered programmatic agent: {agent_name}")
                    
                except (ImportError, AttributeError):
                    # Fallback to markdown-based agent
                    from .markdown_agent import MarkdownAgent
                    
                    config = AgentConfig(
                        name=agent_name,
                        model=agent_info.get("model", "sonnet"),
                        description=agent_info.get("description", ""),
                        capabilities=agent_info.get("preferred_for", []),
                        auto_activate_patterns=agent_info.get("auto_activate_patterns", []),
                        markdown_path=agent_info.get("path")
                    )
                    
                    self.registry.register(agent_name, MarkdownAgent, config)
                    logger.info(f"Registered markdown agent: {agent_name}")
                    
            except Exception as e:
                logger.error(f"Failed to register agent {agent_name}: {e}")
    
    def _get_class_name(self, agent_name: str) -> str:
        """Convert agent name to class name"""
        parts = agent_name.split('-')
        return ''.join(word.capitalize() for word in parts)
    
    async def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent instance by name"""
        if not self._initialized:
            await self.initialize()
        return await self.registry.get_agent(name)
    
    async def orchestrate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run orchestrated workflow"""
        if not self._initialized:
            await self.initialize()
            
        orchestrator = await self.get_agent("mcp-orchestrator")
        if not orchestrator:
            raise RuntimeError("Orchestrator agent not available")
            
        return await orchestrator.process(task)
    
    async def shutdown(self) -> None:
        """Shutdown SDK and cleanup resources"""
        if not self._initialized:
            return
            
        logger.info("Shutting down Claude SDK...")
        
        await self.message_bus.shutdown()
        await self.context_manager.shutdown()
        
        self._initialized = False
        logger.info("Claude SDK shutdown complete")