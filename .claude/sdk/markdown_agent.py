"""
Markdown-based agent for backward compatibility
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent import BaseAgent, AgentConfig, TaskResult

logger = logging.getLogger(__name__)


class MarkdownAgent(BaseAgent):
    """Agent that processes markdown instructions for backward compatibility"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.markdown_content = ""
        self.instructions = {}
        
        if config.markdown_path:
            self._load_markdown_instructions()
    
    def _load_markdown_instructions(self):
        """Load and parse markdown instructions"""
        markdown_path = Path(self.config.markdown_path)
        
        if not markdown_path.exists():
            logger.warning(f"Markdown file not found: {markdown_path}")
            return
        
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                self.markdown_content = f.read()
            
            # Parse key sections
            self.instructions = self._parse_markdown_instructions()
            
            logger.info(f"Loaded markdown instructions for {self.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to load markdown instructions: {e}")
    
    def _parse_markdown_instructions(self) -> Dict[str, Any]:
        """Parse markdown content into structured instructions"""
        instructions = {
            "role": "",
            "capabilities": [],
            "procedures": [],
            "constraints": [],
            "output_formats": []
        }
        
        lines = self.markdown_content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if line.startswith('# Role'):
                current_section = "role"
                current_content = []
            elif line.startswith('# Core Competencies') or line.startswith('# Capabilities'):
                current_section = "capabilities"
                current_content = []
            elif line.startswith('# Standard Operating Procedure') or line.startswith('# SOP'):
                current_section = "procedures"
                current_content = []
            elif line.startswith('# Constraints'):
                current_section = "constraints"
                current_content = []
            elif line.startswith('# Output Format'):
                current_section = "output_formats"
                current_content = []
            elif line.startswith('#'):
                # Other section, continue collecting
                if current_section:
                    current_content.append(line)
            else:
                if current_section and line:
                    current_content.append(line)
        
        # Process collected content
        if current_section and current_content:
            instructions[current_section] = '\n'.join(current_content)
        
        return instructions
    
    async def process(self, task: Dict[str, Any]) -> TaskResult:
        """Process task using markdown instructions"""
        
        # Extract task details
        task_type = task.get("type", "general")
        context = task.get("context", {})
        
        try:
            # Simulate processing based on markdown instructions
            result_data = {
                "agent_type": "markdown",
                "instructions_loaded": bool(self.markdown_content),
                "capabilities": self.config.capabilities,
                "task_type": task_type
            }
            
            # Add specific guidance based on agent type
            if "orchestrator" in self.config.name:
                result_data.update(await self._process_orchestrator_task(task))
            elif "specialist" in self.config.name:
                result_data.update(await self._process_specialist_task(task))
            else:
                result_data.update(await self._process_general_task(task))
            
            return TaskResult(
                task_id="",
                agent_name=self.config.name,
                status="success",
                data=result_data,
                warnings=[
                    f"Using markdown-based fallback for {self.config.name}",
                    "Consider implementing programmatic version for better functionality"
                ]
            )
            
        except Exception as e:
            logger.error(f"Markdown agent error: {e}")
            return TaskResult(
                task_id="",
                agent_name=self.config.name,
                status="error",
                errors=[str(e)]
            )
    
    async def _process_orchestrator_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process orchestrator-specific task"""
        return {
            "message": "Orchestrator task processed using markdown instructions",
            "recommendation": "Implement programmatic orchestrator for full workflow support",
            "fallback_guidance": self._extract_key_guidance("orchestrator")
        }
    
    async def _process_specialist_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process specialist-specific task"""
        return {
            "message": f"Specialist task processed for {self.config.name}",
            "capabilities": self.config.capabilities,
            "guidance": self._extract_key_guidance("specialist")
        }
    
    async def _process_general_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process general task"""
        return {
            "message": f"General task processed by {self.config.name}",
            "instructions": self.instructions.get("role", "No specific role instructions"),
            "capabilities": self.config.capabilities
        }
    
    def _extract_key_guidance(self, agent_type: str) -> List[str]:
        """Extract key guidance from markdown instructions"""
        guidance = []
        
        if agent_type == "orchestrator":
            guidance.extend([
                "Coordinate multi-phase MCP development workflows",
                "Enforce quality gates at each development phase", 
                "Delegate tasks to appropriate specialist agents",
                "Maintain project continuity and context"
            ])
        elif agent_type == "specialist":
            guidance.extend([
                "Provide domain-specific expertise",
                "Follow repository-verified patterns",
                "Ensure implementation quality",
                "Validate against best practices"
            ])
        
        # Add parsed guidance from markdown
        if self.instructions.get("capabilities"):
            guidance.append(f"Capabilities: {self.instructions['capabilities']}")
        
        return guidance
    
    def get_markdown_summary(self) -> Dict[str, Any]:
        """Get summary of loaded markdown instructions"""
        return {
            "agent_name": self.config.name,
            "markdown_path": self.config.markdown_path,
            "content_loaded": bool(self.markdown_content),
            "content_length": len(self.markdown_content),
            "parsed_sections": list(self.instructions.keys()),
            "capabilities": self.config.capabilities
        }