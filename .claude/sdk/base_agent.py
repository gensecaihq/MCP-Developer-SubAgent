"""
Base agent classes and interfaces for the Claude SDK
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import asyncio
import logging
import time
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    model: str  # "opus" or "sonnet"
    description: str
    capabilities: List[str] = field(default_factory=list)
    auto_activate_patterns: List[str] = field(default_factory=list)
    quality_gates: Optional[List[str]] = None
    markdown_path: Optional[str] = None
    max_concurrent_tasks: int = 5
    timeout: float = 300.0  # 5 minutes default
    

@dataclass
class TaskContext:
    """Context for task execution"""
    task_id: str
    agent_name: str
    task_type: str
    input_data: Dict[str, Any]
    created_at: float
    parent_task_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    agent_name: str
    status: str  # "success", "error", "warning"
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.context = {}
        self.logger = self._setup_logger()
        self.active_tasks: Set[str] = set()
        self.message_bus = None
        self.context_manager = None
        self.registry = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup agent-specific logger"""
        logger_name = f"agent.{self.config.name}"
        agent_logger = logging.getLogger(logger_name)
        
        if not agent_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.config.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            agent_logger.addHandler(handler)
            agent_logger.setLevel(logging.INFO)
        
        return agent_logger
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> TaskResult:
        """Process a task and return results"""
        pass
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before processing"""
        # Default validation - can be overridden
        return isinstance(input_data, dict)
    
    async def delegate(self, agent_name: str, task: Dict[str, Any]) -> TaskResult:
        """Delegate task to another agent"""
        if not self.registry:
            raise RuntimeError("Agent registry not available")
            
        target_agent = await self.registry.get_agent(agent_name)
        if not target_agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        self.logger.info(f"Delegating task to {agent_name}")
        return await target_agent.process(task)
    
    async def broadcast(self, message: Dict[str, Any], target_agents: Optional[List[str]] = None):
        """Broadcast message to other agents"""
        if not self.message_bus:
            self.logger.warning("Message bus not available")
            return
            
        from .communication import AgentMessage, MessageType
        
        targets = target_agents or ["all"]
        for target in targets:
            msg = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.BROADCAST,
                source=self.config.name,
                target=target,
                payload=message
            )
            await self.message_bus.publish(msg)
    
    async def save_context(self, context_data: Dict[str, Any]):
        """Save context data"""
        if self.context_manager:
            await self.context_manager.save_context(self.config.name, context_data)
        else:
            self.context.update(context_data)
    
    async def load_context(self) -> Dict[str, Any]:
        """Load context data"""
        if self.context_manager:
            return await self.context_manager.load_context(self.config.name) or {}
        return self.context.copy()
    
    async def execute_with_timeout(self, task: Dict[str, Any]) -> TaskResult:
        """Execute task with timeout handling"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AgentStatus.PROCESSING
            self.active_tasks.add(task_id)
            
            # Validate input
            if not await self.validate_input(task):
                return TaskResult(
                    task_id=task_id,
                    agent_name=self.config.name,
                    status="error",
                    errors=["Input validation failed"],
                    execution_time=time.time() - start_time
                )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.process(task),
                timeout=self.config.timeout
            )
            
            result.task_id = task_id
            result.execution_time = time.time() - start_time
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_id} timed out after {self.config.timeout}s")
            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                status="error",
                errors=[f"Task timed out after {self.config.timeout} seconds"],
                execution_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                status="error",
                errors=[str(e)],
                execution_time=time.time() - start_time
            )
        finally:
            self.status = AgentStatus.IDLE
            self.active_tasks.discard(task_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Return agent health status"""
        return {
            "agent_name": self.config.name,
            "status": self.status.value,
            "active_tasks": len(self.active_tasks),
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "uptime": time.time(),
            "capabilities": self.config.capabilities
        }
    
    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle a specific task type"""
        return task_type in self.config.capabilities
    
    async def initialize(self):
        """Initialize agent (called once after instantiation)"""
        self.logger.info(f"Initializing agent {self.config.name}")
        
    async def shutdown(self):
        """Shutdown agent and cleanup resources"""
        self.logger.info(f"Shutting down agent {self.config.name}")
        
        # Wait for active tasks to complete
        if self.active_tasks:
            self.logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            while self.active_tasks:
                await asyncio.sleep(0.1)


class SpecialistAgent(BaseAgent):
    """Base class for specialist agents"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.expertise_areas = []
        self.tool_registry = {}
    
    def register_tool(self, tool_name: str, tool_func):
        """Register a tool function"""
        self.tool_registry[tool_name] = tool_func
        
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool"""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool {tool_name} not registered")
            
        tool_func = self.tool_registry[tool_name]
        
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**kwargs)
        else:
            return tool_func(**kwargs)
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tool_registry.keys())