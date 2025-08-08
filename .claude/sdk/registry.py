"""
Agent registry and discovery system
"""

from typing import Dict, Type, Optional, List
import importlib
import inspect
import logging
from pathlib import Path

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Dynamic agent registration and discovery"""
    
    def __init__(self):
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._auto_activate_patterns: Dict[str, List[str]] = {}
        
    def register(self, name: str, agent_class: Type[BaseAgent], config: AgentConfig):
        """Register an agent class with configuration"""
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class} must inherit from BaseAgent")
            
        self._agent_classes[name] = agent_class
        self._agent_configs[name] = config
        self._auto_activate_patterns[name] = config.auto_activate_patterns
        
        logger.info(f"Registered agent: {name} (model: {config.model})")
    
    def auto_discover(self, package: str = "claude.agents"):
        """Auto-discover and register agents from package"""
        try:
            # Try to import the package
            package_path = Path(__file__).parent.parent.parent / "claude" / "agents"
            if not package_path.exists():
                logger.warning(f"Package directory not found: {package_path}")
                return
                
            # Scan for Python files
            for py_file in package_path.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                    
                module_name = f"claude.agents.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)
                    
                    # Look for agent classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseAgent) and 
                            obj is not BaseAgent):
                            
                            # Create config from class attributes
                            agent_name = self._class_name_to_agent_name(name)
                            
                            config = AgentConfig(
                                name=agent_name,
                                model=getattr(obj, 'MODEL', 'sonnet'),
                                description=getattr(obj, 'DESCRIPTION', ''),
                                capabilities=getattr(obj, 'CAPABILITIES', []),
                                auto_activate_patterns=getattr(obj, 'AUTO_ACTIVATE_PATTERNS', [])
                            )
                            
                            self.register(agent_name, obj, config)
                            
                except ImportError as e:
                    logger.debug(f"Could not import {module_name}: {e}")
                except Exception as e:
                    logger.error(f"Error processing {module_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")
    
    def _class_name_to_agent_name(self, class_name: str) -> str:
        """Convert class name to agent name"""
        # Convert PascalCase to kebab-case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', class_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    
    async def get_agent(self, name: str, force_new: bool = False) -> Optional[BaseAgent]:
        """Get or create agent instance"""
        if name not in self._agent_classes:
            logger.error(f"Agent {name} not registered")
            return None
            
        # Return existing instance unless forced to create new
        if not force_new and name in self._agent_instances:
            return self._agent_instances[name]
        
        # Create new instance
        try:
            agent_class = self._agent_classes[name]
            config = self._agent_configs[name]
            
            instance = agent_class(config)
            
            # Set up agent dependencies (will be injected by SDK)
            if hasattr(instance, 'registry'):
                instance.registry = self
            
            await instance.initialize()
            
            if not force_new:
                self._agent_instances[name] = instance
                
            logger.info(f"Created agent instance: {name}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            return None
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent names"""
        return list(self._agent_classes.keys())
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        return self._agent_configs.get(name)
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have a specific capability"""
        matching_agents = []
        for name, config in self._agent_configs.items():
            if capability in config.capabilities:
                matching_agents.append(name)
        return matching_agents
    
    def get_agents_by_pattern(self, file_path: str) -> List[str]:
        """Get agents that match file patterns"""
        import fnmatch
        matching_agents = []
        
        for agent_name, patterns in self._auto_activate_patterns.items():
            for pattern in patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    matching_agents.append(agent_name)
                    break
        
        return matching_agents
    
    def get_model_based_agents(self, model: str) -> List[str]:
        """Get agents that use a specific model"""
        matching_agents = []
        for name, config in self._agent_configs.items():
            if config.model == model:
                matching_agents.append(name)
        return matching_agents
    
    def get_agent_stats(self) -> Dict[str, Dict[str, any]]:
        """Get statistics about registered agents"""
        stats = {
            "total_registered": len(self._agent_classes),
            "total_instances": len(self._agent_instances),
            "by_model": {},
            "by_status": {}
        }
        
        # Count by model
        for config in self._agent_configs.values():
            model = config.model
            stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
        
        # Count by status
        for instance in self._agent_instances.values():
            status = instance.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats
    
    async def health_check_all(self) -> Dict[str, Dict[str, any]]:
        """Perform health check on all active agents"""
        health_results = {}
        
        for name, instance in self._agent_instances.items():
            try:
                health_results[name] = await instance.health_check()
            except Exception as e:
                health_results[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_results
    
    async def shutdown_all(self):
        """Shutdown all agent instances"""
        logger.info("Shutting down all agent instances...")
        
        shutdown_tasks = []
        for instance in self._agent_instances.values():
            shutdown_tasks.append(instance.shutdown())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self._agent_instances.clear()
        logger.info("All agent instances shut down")
    
    def unregister(self, name: str):
        """Unregister an agent"""
        if name in self._agent_instances:
            # Should shutdown first
            logger.warning(f"Unregistering active agent instance: {name}")
        
        self._agent_classes.pop(name, None)
        self._agent_configs.pop(name, None)
        self._agent_instances.pop(name, None)
        self._auto_activate_patterns.pop(name, None)
        
        logger.info(f"Unregistered agent: {name}")


class AgentLoader:
    """Utilities for loading agents from various sources"""
    
    @staticmethod
    def load_from_directory(directory: Path, registry: AgentRegistry):
        """Load all agents from a directory"""
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return
        
        for py_file in directory.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                AgentLoader.load_from_file(py_file, registry)
            except Exception as e:
                logger.error(f"Failed to load agent from {py_file}: {e}")
    
    @staticmethod
    def load_from_file(file_path: Path, registry: AgentRegistry):
        """Load agent from a single Python file"""
        spec = importlib.util.spec_from_file_location("agent_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for agent classes
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseAgent) and 
                obj is not BaseAgent):
                
                agent_name = registry._class_name_to_agent_name(name)
                
                config = AgentConfig(
                    name=agent_name,
                    model=getattr(obj, 'MODEL', 'sonnet'),
                    description=getattr(obj, 'DESCRIPTION', ''),
                    capabilities=getattr(obj, 'CAPABILITIES', []),
                    auto_activate_patterns=getattr(obj, 'AUTO_ACTIVATE_PATTERNS', [])
                )
                
                registry.register(agent_name, obj, config)
    
    @staticmethod
    def validate_agent_class(agent_class: Type) -> List[str]:
        """Validate agent class implementation"""
        issues = []
        
        if not issubclass(agent_class, BaseAgent):
            issues.append("Must inherit from BaseAgent")
        
        # Check required methods
        if not hasattr(agent_class, 'process') or not callable(agent_class.process):
            issues.append("Must implement 'process' method")
        
        # Check class attributes
        if not hasattr(agent_class, 'MODEL'):
            issues.append("Should define MODEL class attribute")
        
        if not hasattr(agent_class, 'DESCRIPTION'):
            issues.append("Should define DESCRIPTION class attribute")
        
        return issues