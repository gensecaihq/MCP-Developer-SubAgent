#!/usr/bin/env python3
"""
Comprehensive tests for Claude integration module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_integration import (
    MCPOrchestrator, 
    FastMCPSpecialist,
    MCPProtocolExpert,
    MCPSecurityAuditor,
    MCPPerformanceOptimizer,
    MCPDeploymentSpecialist,
    MCPDebugger,
    ContextManager
)


class TestMCPOrchestrator:
    """Test MCP Orchestrator functionality"""
    
    @pytest.fixture
    def orchestrator(self):
        """Fixture for MCP Orchestrator"""
        return MCPOrchestrator()
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        with patch('claude_integration.anthropic.Anthropic') as mock:
            mock_instance = Mock()
            mock_instance.messages.create = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator.model == "claude-3-opus-20240229"
        assert orchestrator.agent_name == "mcp-orchestrator"
        assert orchestrator.max_tokens > 0
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, orchestrator, mock_anthropic_client):
        """Test conversation creation"""
        session_id = await orchestrator.create_conversation()
        assert session_id is not None
        assert len(session_id) > 0
    
    @pytest.mark.asyncio
    async def test_send_message_basic(self, orchestrator, mock_anthropic_client):
        """Test basic message sending"""
        # Setup mock response
        mock_anthropic_client.messages.create.return_value = Mock(
            content=[Mock(text="Test response")]
        )
        
        await orchestrator.create_conversation()
        result = await orchestrator.send_message("Test message")
        
        assert result["status"] == "success"
        assert "content" in result
        assert mock_anthropic_client.messages.create.called
    
    @pytest.mark.asyncio
    async def test_send_message_with_context(self, orchestrator, mock_anthropic_client):
        """Test message sending with context"""
        mock_anthropic_client.messages.create.return_value = Mock(
            content=[Mock(text="Context response")]
        )
        
        await orchestrator.create_conversation()
        result = await orchestrator.send_message(
            "Create MCP server",
            context="FastMCP implementation needed"
        )
        
        assert result["status"] == "success"
        # Verify context was included in the call
        call_args = mock_anthropic_client.messages.create.call_args
        message_content = str(call_args)
        assert "FastMCP implementation needed" in message_content
    
    @pytest.mark.asyncio
    async def test_send_message_json_format(self, orchestrator, mock_anthropic_client):
        """Test JSON output format"""
        mock_anthropic_client.messages.create.return_value = Mock(
            content=[Mock(text='{"result": "test"}')]
        )
        
        await orchestrator.create_conversation()
        result = await orchestrator.send_message("Test", output_format="json")
        
        assert result["status"] == "success"
        assert isinstance(result["content"], dict)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator, mock_anthropic_client):
        """Test error handling in message sending"""
        mock_anthropic_client.messages.create.side_effect = Exception("API Error")
        
        await orchestrator.create_conversation()
        result = await orchestrator.send_message("Test message")
        
        assert result["status"] == "error"
        assert "API Error" in result["error"]
    
    def test_rate_limiting_integration(self, orchestrator):
        """Test rate limiting is properly integrated"""
        # Verify rate limiter decorator is applied
        assert hasattr(orchestrator.send_message, '__wrapped__')


class TestFastMCPSpecialist:
    """Test FastMCP Specialist functionality"""
    
    @pytest.fixture
    def specialist(self):
        """Fixture for FastMCP Specialist"""
        return FastMCPSpecialist()
    
    def test_specialist_initialization(self, specialist):
        """Test specialist initializes correctly"""
        assert specialist.model == "claude-3-sonnet-20240229"
        assert specialist.agent_name == "fastmcp-specialist"
        assert "FastMCP" in specialist.system_prompt
        assert "Pydantic" in specialist.system_prompt
    
    @pytest.mark.asyncio
    async def test_fastmcp_code_generation(self, specialist):
        """Test FastMCP code generation patterns"""
        with patch.object(specialist, 'client') as mock_client:
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text="""
```python
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("test-server")

@mcp.tool
async def test_tool(param: str) -> str:
    return f"Result: {param}"
```
                """)]
            )
            
            await specialist.create_conversation()
            result = await specialist.send_message("Create a simple FastMCP server")
            
            assert result["status"] == "success"
            content = result["content"]
            assert "@mcp.tool" in content
            assert "FastMCP" in content


class TestMCPSecurityAuditor:
    """Test MCP Security Auditor functionality"""
    
    @pytest.fixture
    def auditor(self):
        """Fixture for Security Auditor"""
        return MCPSecurityAuditor()
    
    def test_auditor_initialization(self, auditor):
        """Test auditor initializes correctly"""
        assert auditor.model == "claude-3-opus-20240229"
        assert auditor.agent_name == "mcp-security-auditor"
        assert "OAuth" in auditor.system_prompt
        assert "security" in auditor.system_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_security_analysis(self, auditor):
        """Test security analysis functionality"""
        with patch.object(auditor, 'client') as mock_client:
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text="""
Security Analysis Results:
- Input validation: REQUIRED
- Authentication: OAuth 2.1 recommended
- Rate limiting: IMPLEMENT
- Audit logging: ENABLE
                """)]
            )
            
            await auditor.create_conversation()
            result = await auditor.send_message("Audit this MCP server for security")
            
            assert result["status"] == "success"
            content = result["content"]
            assert "security" in content.lower() or "Security" in content


class TestMCPPerformanceOptimizer:
    """Test MCP Performance Optimizer functionality"""
    
    @pytest.fixture
    def optimizer(self):
        """Fixture for Performance Optimizer"""
        return MCPPerformanceOptimizer()
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly"""
        assert optimizer.model == "claude-3-sonnet-20240229"
        assert optimizer.agent_name == "mcp-performance-optimizer"
        assert "performance" in optimizer.system_prompt.lower()
        assert "async" in optimizer.system_prompt.lower()


class TestAgentCoordination:
    """Test multi-agent coordination"""
    
    @pytest.fixture
    def orchestrator(self):
        return MCPOrchestrator()
    
    @pytest.fixture
    def context_manager(self):
        return ContextManager()
    
    @pytest.mark.asyncio
    async def test_agent_delegation(self, orchestrator):
        """Test agent delegation patterns"""
        with patch.object(orchestrator, 'client') as mock_client:
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text="Delegating to @fastmcp-specialist for implementation")]
            )
            
            await orchestrator.create_conversation()
            result = await orchestrator.send_message("Create a FastMCP server with security")
            
            assert result["status"] == "success"
            content = result["content"]
            assert "@" in content or "specialist" in content.lower()
    
    @pytest.mark.asyncio
    async def test_context_sharing(self, context_manager):
        """Test context sharing between agents"""
        with patch.object(context_manager, 'client') as mock_client:
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text="Context updated with project state")]
            )
            
            await context_manager.create_conversation()
            result = await context_manager.send_message("Update context with new MCP server")
            
            assert result["status"] == "success"


class TestErrorHandling:
    """Test error handling across all agents"""
    
    @pytest.fixture
    def agents(self):
        """All agent types"""
        return [
            MCPOrchestrator(),
            FastMCPSpecialist(),
            MCPProtocolExpert(),
            MCPSecurityAuditor(),
            MCPPerformanceOptimizer(),
            MCPDeploymentSpecialist(),
            MCPDebugger(),
            ContextManager()
        ]
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, agents):
        """Test API error handling for all agents"""
        for agent in agents:
            with patch.object(agent, 'client') as mock_client:
                mock_client.messages.create.side_effect = Exception("Network error")
                
                await agent.create_conversation()
                result = await agent.send_message("Test message")
                
                assert result["status"] == "error"
                assert "error" in result
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, agents):
        """Test handling of malformed API responses"""
        for agent in agents:
            with patch.object(agent, 'client') as mock_client:
                # Mock malformed response
                mock_response = Mock()
                mock_response.content = []  # Empty content
                mock_client.messages.create.return_value = mock_response
                
                await agent.create_conversation()
                result = await agent.send_message("Test message")
                
                # Should handle gracefully
                assert "status" in result


class TestConfigurationManagement:
    """Test configuration and environment handling"""
    
    def test_api_key_handling(self):
        """Test API key configuration"""
        # Test with environment variable
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            orchestrator = MCPOrchestrator()
            assert orchestrator.client is not None
        
        # Test without environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # Should raise error if no API key
                MCPOrchestrator()
    
    def test_model_configuration(self):
        """Test model configuration for different agents"""
        opus_agents = [MCPOrchestrator(), MCPSecurityAuditor()]
        sonnet_agents = [
            FastMCPSpecialist(), 
            MCPProtocolExpert(),
            MCPPerformanceOptimizer(),
            MCPDeploymentSpecialist(),
            MCPDebugger(),
            ContextManager()
        ]
        
        for agent in opus_agents:
            assert "opus" in agent.model
        
        for agent in sonnet_agents:
            assert "sonnet" in agent.model


class TestSystemPrompts:
    """Test system prompts are properly configured"""
    
    def test_orchestrator_prompt(self):
        """Test orchestrator system prompt"""
        orchestrator = MCPOrchestrator()
        prompt = orchestrator.system_prompt
        
        assert "orchestrator" in prompt.lower()
        assert "quality gates" in prompt.lower()
        assert "workflow" in prompt.lower()
    
    def test_specialist_prompts(self):
        """Test specialist agent prompts"""
        specialists = {
            FastMCPSpecialist(): ["fastmcp", "pydantic", "decorator"],
            MCPProtocolExpert(): ["protocol", "json-rpc", "transport"],
            MCPSecurityAuditor(): ["oauth", "security", "authentication"],
            MCPPerformanceOptimizer(): ["performance", "async", "optimization"],
            MCPDeploymentSpecialist(): ["deployment", "docker", "kubernetes"],
            MCPDebugger(): ["debug", "troubleshoot", "diagnostic"],
            ContextManager(): ["context", "state", "coordination"]
        }
        
        for agent, keywords in specialists.items():
            prompt = agent.system_prompt.lower()
            for keyword in keywords:
                assert keyword in prompt, f"Missing {keyword} in {agent.agent_name} prompt"


# Test utilities for external use
class MockClaude:
    """Mock Claude client for testing"""
    
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0
    
    def add_response(self, prompt_pattern: str, response: str):
        """Add a mock response for a prompt pattern"""
        self.responses[prompt_pattern] = response
    
    async def mock_create(self, **kwargs):
        """Mock the messages.create call"""
        self.call_count += 1
        
        # Find matching response
        messages = kwargs.get('messages', [])
        if messages:
            content = messages[-1].get('content', '')
            for pattern, response in self.responses.items():
                if pattern.lower() in content.lower():
                    return Mock(content=[Mock(text=response)])
        
        # Default response
        return Mock(content=[Mock(text="Mock response")])


class AgentTestHarness:
    """Test harness for agent testing"""
    
    def __init__(self, agent_class):
        self.agent_class = agent_class
        self.mock_claude = MockClaude()
    
    async def test_agent_workflow(self, test_messages):
        """Test a complete agent workflow"""
        agent = self.agent_class()
        
        with patch.object(agent, 'client') as mock_client:
            mock_client.messages.create = self.mock_claude.mock_create
            
            await agent.create_conversation()
            
            results = []
            for message in test_messages:
                result = await agent.send_message(message)
                results.append(result)
            
            return results


def run_integration_tests():
    """Run integration tests for all agents"""
    return pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_integration_tests()