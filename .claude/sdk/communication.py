"""
Inter-agent communication framework
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable
import uuid
import asyncio
import time
import logging
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    DELEGATE = "delegate"
    BROADCAST = "broadcast"
    ERROR = "error"
    NOTIFICATION = "notification"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentMessage:
    """Message passed between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    source: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MessageType(data.get("type", "request")),
            source=data.get("source", ""),
            target=data.get("target", ""),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            timestamp=data.get("timestamp", time.time()),
            priority=MessagePriority(data.get("priority", 2)),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {})
        )


class MessageHandler:
    """Handler for processing messages"""
    
    def __init__(self, handler_func: Callable, message_types: List[MessageType], priority: int = 0):
        self.handler_func = handler_func
        self.message_types = message_types
        self.priority = priority
        self.call_count = 0
        self.error_count = 0
        
    async def handle(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle a message"""
        if message.type not in self.message_types:
            return None
            
        try:
            self.call_count += 1
            
            if asyncio.iscoroutinefunction(self.handler_func):
                result = await self.handler_func(message)
            else:
                result = self.handler_func(message)
            
            # If handler returns a dict, wrap in response message
            if isinstance(result, dict):
                return AgentMessage(
                    type=MessageType.RESPONSE,
                    source=message.target,
                    target=message.source,
                    payload=result,
                    correlation_id=message.id
                )
            elif isinstance(result, AgentMessage):
                return result
                
            return None
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Message handler error: {e}")
            
            return AgentMessage(
                type=MessageType.ERROR,
                source=message.target,
                target=message.source,
                payload={"error": str(e)},
                correlation_id=message.id
            )


class MessageQueue:
    """Priority-based message queue"""
    
    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._queues = {
            MessagePriority.URGENT: asyncio.Queue(),
            MessagePriority.HIGH: asyncio.Queue(),
            MessagePriority.NORMAL: asyncio.Queue(),
            MessagePriority.LOW: asyncio.Queue()
        }
        self._size = 0
        
    async def put(self, message: AgentMessage):
        """Add message to queue"""
        if self._size >= self.maxsize:
            raise asyncio.QueueFull("Message queue is full")
            
        await self._queues[message.priority].put(message)
        self._size += 1
    
    async def get(self) -> AgentMessage:
        """Get next message by priority"""
        # Check queues in priority order
        for priority in [MessagePriority.URGENT, MessagePriority.HIGH, 
                        MessagePriority.NORMAL, MessagePriority.LOW]:
            queue = self._queues[priority]
            if not queue.empty():
                message = await queue.get()
                self._size -= 1
                return message
        
        # If all queues empty, wait on normal priority
        message = await self._queues[MessagePriority.NORMAL].get()
        self._size -= 1
        return message
    
    def qsize(self) -> int:
        """Get total queue size"""
        return self._size
    
    def empty(self) -> bool:
        """Check if all queues are empty"""
        return self._size == 0


class MessageBus:
    """Async message bus for inter-agent communication"""
    
    def __init__(self):
        self._agent_queues: Dict[str, MessageQueue] = {}
        self._handlers: Dict[str, List[MessageHandler]] = {}
        self._running = False
        self._worker_tasks = []
        self._message_stats = {
            "sent": 0,
            "received": 0,
            "errors": 0,
            "timeouts": 0
        }
        
    async def initialize(self):
        """Initialize message bus"""
        if self._running:
            return
            
        self._running = True
        logger.info("Message bus initialized")
    
    async def register_agent(self, agent_name: str):
        """Register agent with message bus"""
        if agent_name not in self._agent_queues:
            self._agent_queues[agent_name] = MessageQueue()
            self._handlers[agent_name] = []
            
            # Start worker task for this agent
            worker = asyncio.create_task(self._message_worker(agent_name))
            self._worker_tasks.append(worker)
            
            logger.info(f"Registered agent with message bus: {agent_name}")
    
    async def unregister_agent(self, agent_name: str):
        """Unregister agent from message bus"""
        if agent_name in self._agent_queues:
            del self._agent_queues[agent_name]
            del self._handlers[agent_name]
            logger.info(f"Unregistered agent from message bus: {agent_name}")
    
    async def _message_worker(self, agent_name: str):
        """Worker task to process messages for an agent"""
        queue = self._agent_queues.get(agent_name)
        if not queue:
            return
            
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._process_message(agent_name, message)
                self._message_stats["received"] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message worker error for {agent_name}: {e}")
                self._message_stats["errors"] += 1
                await asyncio.sleep(0.1)
    
    async def _process_message(self, agent_name: str, message: AgentMessage):
        """Process a message for an agent"""
        handlers = self._handlers.get(agent_name, [])
        
        if not handlers:
            logger.warning(f"No handlers for agent {agent_name}")
            return
        
        # Sort handlers by priority
        sorted_handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)
        
        # Try each handler
        for handler in sorted_handlers:
            try:
                response = await handler.handle(message)
                if response:
                    await self.publish(response)
                    break
            except Exception as e:
                logger.error(f"Handler error: {e}")
                continue
    
    async def publish(self, message: AgentMessage):
        """Publish message to target agent"""
        if not self._running:
            raise RuntimeError("Message bus not running")
        
        target = message.target
        
        # Handle broadcast messages
        if target == "all":
            for agent_name in self._agent_queues:
                if agent_name != message.source:
                    broadcast_msg = AgentMessage(**message.__dict__)
                    broadcast_msg.target = agent_name
                    await self._agent_queues[agent_name].put(broadcast_msg)
            return
        
        # Handle targeted messages
        if target not in self._agent_queues:
            logger.error(f"Target agent not found: {target}")
            return
        
        try:
            await self._agent_queues[target].put(message)
            self._message_stats["sent"] += 1
            
        except asyncio.QueueFull:
            logger.error(f"Queue full for agent {target}")
            self._message_stats["errors"] += 1
    
    def add_handler(self, agent_name: str, handler: MessageHandler):
        """Add message handler for an agent"""
        if agent_name not in self._handlers:
            self._handlers[agent_name] = []
        
        self._handlers[agent_name].append(handler)
        logger.debug(f"Added handler for {agent_name}")
    
    def remove_handler(self, agent_name: str, handler: MessageHandler):
        """Remove message handler"""
        if agent_name in self._handlers:
            try:
                self._handlers[agent_name].remove(handler)
                logger.debug(f"Removed handler for {agent_name}")
            except ValueError:
                pass
    
    async def request_response(self, message: AgentMessage, timeout: float = 30) -> Optional[AgentMessage]:
        """Send request and wait for response"""
        correlation_id = message.id
        response_queue = asyncio.Queue()
        
        # Create temporary handler for response
        def response_handler(msg: AgentMessage):
            if (msg.type == MessageType.RESPONSE and 
                msg.correlation_id == correlation_id):
                response_queue.put_nowait(msg)
                return True
            return False
        
        handler = MessageHandler(
            response_handler, 
            [MessageType.RESPONSE], 
            priority=100  # High priority for response handling
        )
        
        self.add_handler(message.source, handler)
        
        try:
            await self.publish(message)
            response = await asyncio.wait_for(response_queue.get(), timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {message.id}")
            self._message_stats["timeouts"] += 1
            return None
            
        finally:
            self.remove_handler(message.source, handler)
    
    async def subscribe(self, agent_name: str) -> MessageQueue:
        """Subscribe agent to receive messages"""
        await self.register_agent(agent_name)
        return self._agent_queues[agent_name]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        queue_stats = {}
        for agent_name, queue in self._agent_queues.items():
            queue_stats[agent_name] = {
                "queue_size": queue.qsize(),
                "handler_count": len(self._handlers.get(agent_name, []))
            }
        
        return {
            "message_stats": self._message_stats.copy(),
            "active_agents": len(self._agent_queues),
            "worker_tasks": len(self._worker_tasks),
            "queue_stats": queue_stats
        }
    
    async def shutdown(self):
        """Shutdown message bus"""
        if not self._running:
            return
            
        logger.info("Shutting down message bus...")
        self._running = False
        
        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        self._agent_queues.clear()
        self._handlers.clear()
        
        logger.info("Message bus shut down")