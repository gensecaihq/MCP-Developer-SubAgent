#!/usr/bin/env python3
"""
Enhanced Cross-Agent Activation Engine
Intelligently activates and coordinates sub-agents based on multiple factors
"""

import json
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

@dataclass
class ActivationContext:
    """Context for agent activation decisions"""
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    project_phase: Optional[str] = None
    recent_errors: List[str] = None
    active_agents: Set[str] = None
    user_request: Optional[str] = None
    project_state: Dict = None
    
    def __post_init__(self):
        if self.recent_errors is None:
            self.recent_errors = []
        if self.active_agents is None:
            self.active_agents = set()
        if self.project_state is None:
            self.project_state = {}

class CrossAgentActivationEngine:
    """
    Intelligent activation engine that determines which agents to activate
    based on multiple factors including content, context, and workflow phase
    """
    
    def __init__(self, rules_path: str = ".claude/activation_rules.json"):
        self.rules_path = Path(rules_path)
        self.activation_rules = self._load_rules()
        self.activation_history = defaultdict(list)
        self.learning_data = defaultdict(int)
        
    def _load_rules(self) -> Dict:
        """Load activation rules from JSON configuration"""
        if self.rules_path.exists():
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        return {}
    
    def analyze_activation_needs(self, context: ActivationContext) -> List[Tuple[str, float, str]]:
        """
        Analyze the context and determine which agents should be activated
        Returns: List of (agent_name, priority_score, reason) tuples
        """
        activations = []
        
        # 1. Content-based activation
        if context.file_content:
            content_activations = self._analyze_content(context.file_content)
            activations.extend(content_activations)
        
        # 2. File pattern-based activation
        if context.file_path:
            pattern_activations = self._analyze_file_patterns(context.file_path)
            activations.extend(pattern_activations)
        
        # 3. Context-aware activation
        if context.project_state:
            context_activations = self._analyze_project_context(context)
            activations.extend(context_activations)
        
        # 4. Workflow phase-based activation
        if context.project_phase:
            phase_activations = self._analyze_workflow_phase(context.project_phase)
            activations.extend(phase_activations)
        
        # 5. Error-driven activation
        if context.recent_errors:
            error_activations = self._analyze_errors(context.recent_errors)
            activations.extend(error_activations)
        
        # 6. User request analysis
        if context.user_request:
            request_activations = self._analyze_user_request(context.user_request)
            activations.extend(request_activations)
        
        # Deduplicate and prioritize
        return self._prioritize_activations(activations, context)
    
    def _analyze_content(self, content: str) -> List[Tuple[str, float, str]]:
        """Analyze file content to determine agent activation"""
        activations = []
        
        content_rules = self.activation_rules.get('activation_rules', {}).get('content_based_activation', {}).get('rules', [])
        
        for rule in content_rules:
            pattern = rule.get('pattern', '')
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                priority_map = {'critical': 1.0, 'high': 0.8, 'medium': 0.5, 'low': 0.3}
                score = priority_map.get(rule.get('priority', 'medium'), 0.5)
                
                for agent in rule.get('agents', []):
                    activations.append((agent, score, rule.get('reason', 'Content pattern matched')))
        
        return activations
    
    def _analyze_file_patterns(self, file_path: str) -> List[Tuple[str, float, str]]:
        """Analyze file path patterns for agent activation"""
        activations = []
        path = Path(file_path)
        
        # Check against existing config patterns
        # This would integrate with the existing config.json patterns
        pattern_map = {
            'server.py': [('mcp-orchestrator', 0.9, 'Main server file')],
            'auth': [('mcp-security-auditor', 0.8, 'Authentication file')],
            'test': [('mcp-debugger', 0.7, 'Test file detected')],
            'docker': [('mcp-deployment-specialist', 0.8, 'Docker configuration')],
            'performance': [('mcp-performance-optimizer', 0.7, 'Performance-related file')],
        }
        
        for pattern, agents in pattern_map.items():
            if pattern in str(path).lower():
                activations.extend(agents)
        
        return activations
    
    def _analyze_project_context(self, context: ActivationContext) -> List[Tuple[str, float, str]]:
        """Analyze project context for intelligent activation"""
        activations = []
        
        context_rules = self.activation_rules.get('activation_rules', {}).get('context_aware_activation', {}).get('rules', [])
        
        for rule in context_rules:
            if self._evaluate_condition(rule.get('condition', ''), context):
                agents = rule.get('agents', [])
                reason = rule.get('reason', 'Context condition met')
                
                # Higher priority for context-aware activations
                for i, agent in enumerate(agents):
                    score = 0.9 - (i * 0.1)  # Decreasing score for sequence
                    activations.append((agent, score, reason))
        
        return activations
    
    def _analyze_workflow_phase(self, phase: str) -> List[Tuple[str, float, str]]:
        """Activate agents based on workflow phase"""
        activations = []
        
        phases = self.activation_rules.get('activation_rules', {}).get('workflow_based_activation', {}).get('phases', [])
        
        for phase_config in phases:
            if phase_config.get('phase') == phase:
                agents = phase_config.get('agents', [])
                for agent in agents:
                    activations.append((agent, 0.85, f'Workflow phase: {phase}'))
        
        return activations
    
    def _analyze_errors(self, errors: List[str]) -> List[Tuple[str, float, str]]:
        """Analyze errors to activate debugging and related agents"""
        activations = []
        
        if errors:
            # Always activate debugger for errors
            activations.append(('mcp-debugger', 0.95, 'Errors detected'))
            
            # Check error types for specific agents
            error_text = ' '.join(errors).lower()
            
            if 'performance' in error_text or 'timeout' in error_text:
                activations.append(('mcp-performance-optimizer', 0.8, 'Performance issues detected'))
            
            if 'auth' in error_text or 'permission' in error_text:
                activations.append(('mcp-security-auditor', 0.8, 'Security issues detected'))
            
            if 'connection' in error_text or 'protocol' in error_text:
                activations.append(('mcp-protocol-expert', 0.7, 'Protocol issues detected'))
        
        return activations
    
    def _analyze_user_request(self, request: str) -> List[Tuple[str, float, str]]:
        """Analyze user request to determine which agents to activate"""
        activations = []
        request_lower = request.lower()
        
        # Keywords to agent mapping
        keyword_map = {
            'orchestrate': ('mcp-orchestrator', 0.95),
            'coordinate': ('mcp-orchestrator', 0.9),
            'implement': ('fastmcp-specialist', 0.9),
            'security': ('mcp-security-auditor', 0.95),
            'auth': ('mcp-security-auditor', 0.9),
            'performance': ('mcp-performance-optimizer', 0.9),
            'optimize': ('mcp-performance-optimizer', 0.85),
            'deploy': ('mcp-deployment-specialist', 0.9),
            'docker': ('mcp-deployment-specialist', 0.85),
            'debug': ('mcp-debugger', 0.95),
            'error': ('mcp-debugger', 0.85),
            'protocol': ('mcp-protocol-expert', 0.9),
            'transport': ('mcp-protocol-expert', 0.85),
        }
        
        for keyword, (agent, score) in keyword_map.items():
            if keyword in request_lower:
                activations.append((agent, score, f'User requested: {keyword}'))
        
        # Always include context manager for complex requests
        if len(request.split()) > 20:
            activations.append(('context-manager', 0.7, 'Complex request - context needed'))
        
        return activations
    
    def _evaluate_condition(self, condition: str, context: ActivationContext) -> bool:
        """Evaluate a condition against the context"""
        condition_evaluators = {
            'new_project': lambda ctx: not ctx.project_state.get('initialized', False),
            'multiple_tools_defined': lambda ctx: ctx.project_state.get('tool_count', 0) > 3,
            'external_api_calls': lambda ctx: 'http' in str(ctx.file_content).lower() if ctx.file_content else False,
            'production_ready': lambda ctx: ctx.project_phase == 'deployment',
            'performance_issues': lambda ctx: any('performance' in err.lower() for err in ctx.recent_errors),
        }
        
        evaluator = condition_evaluators.get(condition)
        return evaluator(context) if evaluator else False
    
    def _prioritize_activations(self, activations: List[Tuple[str, float, str]], 
                               context: ActivationContext) -> List[Tuple[str, float, str]]:
        """Prioritize and deduplicate agent activations"""
        # Aggregate scores by agent
        agent_scores = defaultdict(list)
        agent_reasons = defaultdict(set)
        
        for agent, score, reason in activations:
            agent_scores[agent].append(score)
            agent_reasons[agent].add(reason)
        
        # Calculate final scores
        final_activations = []
        for agent, scores in agent_scores.items():
            # Use a weighted average favoring higher scores
            final_score = max(scores) * 0.7 + (sum(scores) / len(scores)) * 0.3
            
            # Boost score based on learning data
            if agent in self.learning_data:
                boost = min(self.learning_data[agent] * 0.02, 0.2)  # Max 20% boost
                final_score = min(final_score + boost, 1.0)
            
            # Compile reasons
            reasons = ' | '.join(agent_reasons[agent])
            
            final_activations.append((agent, final_score, reasons))
        
        # Sort by score and apply activation threshold
        threshold = self.activation_rules.get('activation_settings', {}).get('activation_threshold', 0.7)
        filtered = [(a, s, r) for a, s, r in final_activations if s >= threshold]
        
        # Limit concurrent agents
        max_concurrent = self.activation_rules.get('activation_settings', {}).get('max_concurrent_agents', 3)
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        return filtered[:max_concurrent]
    
    def get_delegation_chain(self, from_agent: str, context: ActivationContext) -> List[str]:
        """Get the delegation chain from one agent to others"""
        delegations = self.activation_rules.get('activation_rules', {}).get('intelligent_delegation', {}).get('delegation_chains', [])
        
        chain = []
        for delegation in delegations:
            if delegation.get('from') == from_agent:
                condition = delegation.get('condition', '')
                if self._evaluate_condition(condition, context):
                    chain.extend(delegation.get('to', []))
        
        return chain
    
    def get_collaboration_pattern(self, trigger: str) -> Optional[Dict]:
        """Get multi-agent collaboration pattern for a trigger"""
        patterns = self.activation_rules.get('activation_rules', {}).get('multi_agent_collaboration', {}).get('collaboration_patterns', [])
        
        for pattern in patterns:
            if trigger.lower() in pattern.get('trigger', '').lower():
                return pattern
        
        return None
    
    def record_activation_success(self, agent: str, context: ActivationContext):
        """Record successful activation for learning"""
        self.activation_history[agent].append({
            'timestamp': None,  # Would use datetime in real implementation
            'context': context.project_phase,
            'success': True
        })
        self.learning_data[agent] += 1
    
    def generate_activation_report(self, activations: List[Tuple[str, float, str]]) -> str:
        """Generate a human-readable activation report"""
        if not activations:
            return "No agents activated based on current context."
        
        report = "## 🤖 Agent Activation Report\n\n"
        report += "### Activated Agents:\n"
        
        for agent, score, reason in activations:
            confidence = "High" if score > 0.8 else "Medium" if score > 0.6 else "Low"
            report += f"- **{agent}** (Confidence: {confidence} - {score:.2f})\n"
            report += f"  - Reason: {reason}\n"
        
        # Add delegation information if applicable
        if len(activations) > 1:
            report += "\n### Coordination Strategy:\n"
            lead_agent = activations[0][0]
            report += f"- Lead Agent: {lead_agent}\n"
            report += f"- Supporting Agents: {', '.join([a for a, _, _ in activations[1:]])}\n"
        
        return report


# Example usage
def demonstrate_activation():
    """Demonstrate the enhanced activation system"""
    engine = CrossAgentActivationEngine()
    
    # Example 1: New FastMCP server with authentication
    context1 = ActivationContext(
        file_path="server.py",
        file_content="""
from fastmcp import FastMCP
from pydantic import BaseModel
import jwt

mcp = FastMCP("my-server")

@mcp.tool
async def authenticate_user(token: str):
    # OAuth implementation
    pass
        """,
        project_phase="implementation",
        user_request="Help me implement a secure MCP server with authentication"
    )
    
    activations1 = engine.analyze_activation_needs(context1)
    print("Example 1: FastMCP Server with Auth")
    print(engine.generate_activation_report(activations1))
    print()
    
    # Example 2: Performance issues
    context2 = ActivationContext(
        recent_errors=["Timeout error", "Connection pool exhausted"],
        project_phase="optimization",
        user_request="My MCP server is running slowly"
    )
    
    activations2 = engine.analyze_activation_needs(context2)
    print("Example 2: Performance Issues")
    print(engine.generate_activation_report(activations2))
    print()
    
    # Example 3: Production deployment
    context3 = ActivationContext(
        file_path="Dockerfile",
        project_phase="deployment",
        project_state={"production_ready": True},
        user_request="Deploy my MCP server to production"
    )
    
    activations3 = engine.analyze_activation_needs(context3)
    print("Example 3: Production Deployment")
    print(engine.generate_activation_report(activations3))


if __name__ == "__main__":
    demonstrate_activation()