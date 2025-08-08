"""
Auto-activation system for intelligent agent selection
"""

import fnmatch
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ActivationScore:
    """Represents an activation score for an agent"""
    agent_name: str
    score: float
    reasons: List[str]
    confidence: float


class PatternMatcher:
    """Intelligent pattern matching for auto-activation"""
    
    def __init__(self):
        self.compiled_patterns = {}
        
    def register_patterns(self, agent_name: str, patterns: List[str]):
        """Register file patterns for an agent"""
        compiled = []
        for pattern in patterns:
            if pattern.startswith("regex:"):
                compiled.append(("regex", re.compile(pattern[6:])))
            else:
                compiled.append(("glob", pattern))
        
        self.compiled_patterns[agent_name] = compiled
        logger.debug(f"Registered {len(patterns)} patterns for {agent_name}")
    
    def match_file(self, file_path: str) -> List[str]:
        """Find agents that match the file path"""
        matching_agents = []
        path = Path(file_path)
        
        for agent_name, patterns in self.compiled_patterns.items():
            for pattern_type, pattern in patterns:
                try:
                    if pattern_type == "glob":
                        if fnmatch.fnmatch(str(path), pattern):
                            matching_agents.append(agent_name)
                            break
                    elif pattern_type == "regex":
                        if pattern.search(str(path)):
                            matching_agents.append(agent_name)
                            break
                except Exception as e:
                    logger.warning(f"Pattern matching error for {agent_name}: {e}")
        
        return matching_agents
    
    def analyze_content(self, file_content: str) -> Dict[str, float]:
        """Analyze file content to determine agent relevance"""
        # Define context indicators with weights
        indicators = {
            "mcp-orchestrator": {
                "keywords": ["workflow", "orchestrate", "quality", "gate", "phase"],
                "patterns": [r"mcp.*workflow", r"quality.*gate"],
                "weight": 1.0
            },
            "mcp-protocol-expert": {
                "keywords": ["JSON-RPC", "transport", "capability", "stdio", "jsonrpc", "2.0"],
                "patterns": [r"jsonrpc.*2\.0", r"transport.*layer", r"capability.*negotiation"],
                "weight": 1.2
            },
            "fastmcp-specialist": {
                "keywords": ["@mcp.tool", "FastMCP", "pydantic", "BaseModel", "decorator"],
                "patterns": [r"@mcp\.(tool|resource|prompt)", r"FastMCP\(", r"class.*BaseModel"],
                "weight": 1.3
            },
            "mcp-security-auditor": {
                "keywords": ["OAuth", "JWT", "authentication", "security", "token", "auth"],
                "patterns": [r"oauth.*2\.[01]", r"jwt.*decode", r"security.*audit"],
                "weight": 1.1
            },
            "mcp-performance-optimizer": {
                "keywords": ["async", "await", "pool", "cache", "performance", "optimize"],
                "patterns": [r"async\s+def", r"connection.*pool", r"cache.*strategy"],
                "weight": 1.0
            },
            "mcp-deployment-specialist": {
                "keywords": ["docker", "kubernetes", "deploy", "container", "k8s"],
                "patterns": [r"FROM\s+\w+", r"kind:\s*Deployment", r"docker.*compose"],
                "weight": 0.9
            },
            "mcp-debugger": {
                "keywords": ["debug", "test", "error", "trace", "log"],
                "patterns": [r"def\s+test_", r"pytest", r"logger\.", r"raise.*Exception"],
                "weight": 0.8
            }
        }
        
        relevance_scores = {}
        content_lower = file_content.lower()
        
        for agent, config in indicators.items():
            score = 0.0
            reasons = []
            
            # Check keywords
            keyword_matches = 0
            for keyword in config["keywords"]:
                if keyword.lower() in content_lower:
                    keyword_matches += 1
                    reasons.append(f"keyword: {keyword}")
            
            if keyword_matches > 0:
                keyword_score = min(keyword_matches / len(config["keywords"]), 1.0)
                score += keyword_score * 0.6
            
            # Check patterns
            pattern_matches = 0
            for pattern in config["patterns"]:
                try:
                    if re.search(pattern, file_content, re.IGNORECASE):
                        pattern_matches += 1
                        reasons.append(f"pattern: {pattern}")
                except Exception as e:
                    logger.warning(f"Pattern matching error: {e}")
            
            if pattern_matches > 0:
                pattern_score = min(pattern_matches / len(config["patterns"]), 1.0)
                score += pattern_score * 0.4
            
            # Apply weight
            final_score = score * config["weight"]
            
            if final_score > 0.1:  # Only include relevant scores
                relevance_scores[agent] = final_score
        
        return relevance_scores
    
    def analyze_task_context(self, task: Dict[str, Any]) -> Dict[str, float]:
        """Analyze task context for agent relevance"""
        task_type = task.get("type", "").lower()
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        # Task type mapping
        type_mapping = {
            "orchestrate": {"mcp-orchestrator": 1.0},
            "workflow": {"mcp-orchestrator": 1.0},
            "implement": {"fastmcp-specialist": 0.9},
            "create": {"fastmcp-specialist": 0.8},
            "security": {"mcp-security-auditor": 1.0},
            "audit": {"mcp-security-auditor": 0.9},
            "optimize": {"mcp-performance-optimizer": 1.0},
            "performance": {"mcp-performance-optimizer": 1.0},
            "deploy": {"mcp-deployment-specialist": 1.0},
            "debug": {"mcp-debugger": 1.0},
            "test": {"mcp-debugger": 0.8},
            "protocol": {"mcp-protocol-expert": 1.0}
        }
        
        scores = {}
        
        # Check task type
        for keyword, agents in type_mapping.items():
            if keyword in task_type:
                for agent, score in agents.items():
                    scores[agent] = scores.get(agent, 0) + score
        
        # Check requirements
        if isinstance(requirements, dict):
            if requirements.get("authentication"):
                scores["mcp-security-auditor"] = scores.get("mcp-security-auditor", 0) + 0.7
            
            if requirements.get("tools") or requirements.get("resources"):
                scores["fastmcp-specialist"] = scores.get("fastmcp-specialist", 0) + 0.6
            
            if requirements.get("transport"):
                scores["mcp-protocol-expert"] = scores.get("mcp-protocol-expert", 0) + 0.5
        
        return scores


class AutoActivationManager:
    """Manages automatic agent activation"""
    
    def __init__(self, registry):
        self.registry = registry
        self.pattern_matcher = PatternMatcher()
        self.activation_threshold = 0.3
        self.max_suggestions = 5
        
        # Load patterns from registry
        self._load_agent_patterns()
    
    def _load_agent_patterns(self):
        """Load agent patterns from registry"""
        for agent_name in self.registry.get_registered_agents():
            config = self.registry.get_agent_config(agent_name)
            if config and config.auto_activate_patterns:
                self.pattern_matcher.register_patterns(
                    agent_name, 
                    config.auto_activate_patterns
                )
    
    async def suggest_agents_for_file(self, file_path: str, 
                                    content: Optional[str] = None) -> List[ActivationScore]:
        """Suggest agents based on file analysis"""
        suggestions = []
        
        # Pattern-based matching
        pattern_matches = self.pattern_matcher.match_file(file_path)
        for agent_name in pattern_matches:
            suggestions.append(ActivationScore(
                agent_name=agent_name,
                score=0.8,
                reasons=[f"file pattern match: {file_path}"],
                confidence=0.9
            ))
        
        # Content-based matching
        if content:
            content_scores = self.pattern_matcher.analyze_content(content)
            for agent_name, score in content_scores.items():
                if score >= self.activation_threshold:
                    # Check if already suggested from patterns
                    existing = next((s for s in suggestions if s.agent_name == agent_name), None)
                    if existing:
                        # Boost existing suggestion
                        existing.score = min(existing.score + score * 0.3, 1.0)
                        existing.reasons.append("content analysis")
                        existing.confidence = min(existing.confidence + 0.1, 1.0)
                    else:
                        suggestions.append(ActivationScore(
                            agent_name=agent_name,
                            score=score,
                            reasons=["content analysis"],
                            confidence=score * 0.8
                        ))
        
        # Sort by score and limit results
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:self.max_suggestions]
    
    async def suggest_agents_for_task(self, task: Dict[str, Any]) -> List[ActivationScore]:
        """Suggest agents based on task analysis"""
        suggestions = []
        
        # Task context analysis
        context_scores = self.pattern_matcher.analyze_task_context(task)
        
        for agent_name, score in context_scores.items():
            if score >= self.activation_threshold:
                # Get agent capabilities for reason generation
                config = self.registry.get_agent_config(agent_name)
                capabilities = config.capabilities if config else []
                
                reasons = [f"task analysis score: {score:.2f}"]
                if capabilities:
                    reasons.append(f"capabilities: {', '.join(capabilities[:3])}")
                
                suggestions.append(ActivationScore(
                    agent_name=agent_name,
                    score=min(score, 1.0),
                    reasons=reasons,
                    confidence=score * 0.7
                ))
        
        # Always suggest orchestrator for complex tasks
        if not any(s.agent_name == "mcp-orchestrator" for s in suggestions):
            task_complexity = self._assess_task_complexity(task)
            if task_complexity > 0.5:
                suggestions.append(ActivationScore(
                    agent_name="mcp-orchestrator",
                    score=task_complexity,
                    reasons=["complex task requiring orchestration"],
                    confidence=0.8
                ))
        
        # Sort by score and limit results
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:self.max_suggestions]
    
    def _assess_task_complexity(self, task: Dict[str, Any]) -> float:
        """Assess task complexity for orchestrator suggestion"""
        complexity_indicators = {
            "multiple_phases": 0.3,
            "multiple_agents": 0.3,
            "quality_gates": 0.2,
            "workflow": 0.4,
            "orchestrate": 0.5,
            "coordinate": 0.3,
            "manage": 0.2
        }
        
        task_str = str(task).lower()
        complexity_score = 0.0
        
        for indicator, weight in complexity_indicators.items():
            if indicator in task_str:
                complexity_score += weight
        
        # Check for requirements complexity
        requirements = task.get("requirements", {})
        if isinstance(requirements, dict):
            num_requirements = len(requirements)
            if num_requirements > 3:
                complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    async def auto_activate_agents(self, file_path: Optional[str] = None, 
                                 content: Optional[str] = None,
                                 task: Optional[Dict[str, Any]] = None) -> List[str]:
        """Auto-activate agents based on context"""
        activated_agents = []
        
        try:
            suggestions = []
            
            # Get suggestions based on available context
            if file_path or content:
                file_suggestions = await self.suggest_agents_for_file(file_path or "", content)
                suggestions.extend(file_suggestions)
            
            if task:
                task_suggestions = await self.suggest_agents_for_task(task)
                suggestions.extend(task_suggestions)
            
            # Remove duplicates and sort
            unique_suggestions = {}
            for suggestion in suggestions:
                if suggestion.agent_name not in unique_suggestions:
                    unique_suggestions[suggestion.agent_name] = suggestion
                else:
                    # Merge suggestions for same agent
                    existing = unique_suggestions[suggestion.agent_name]
                    existing.score = max(existing.score, suggestion.score)
                    existing.reasons.extend(suggestion.reasons)
                    existing.confidence = max(existing.confidence, suggestion.confidence)
            
            # Activate agents above threshold
            for agent_name, suggestion in unique_suggestions.items():
                if suggestion.score >= self.activation_threshold:
                    # Check if agent exists
                    if agent_name in self.registry.get_registered_agents():
                        activated_agents.append(agent_name)
                        logger.info(f"Auto-activated {agent_name} (score: {suggestion.score:.2f})")
            
        except Exception as e:
            logger.error(f"Auto-activation error: {e}")
        
        return activated_agents
    
    def get_activation_stats(self) -> Dict[str, Any]:
        """Get auto-activation statistics"""
        return {
            "threshold": self.activation_threshold,
            "max_suggestions": self.max_suggestions,
            "registered_patterns": len(self.pattern_matcher.compiled_patterns),
            "available_agents": len(self.registry.get_registered_agents())
        }