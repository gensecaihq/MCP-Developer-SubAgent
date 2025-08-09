#!/usr/bin/env python3
"""
Test utilities and helper functions for comprehensive testing
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def create_temp_project() -> Path:
        """Create a temporary project directory with basic structure"""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create basic project structure
        (temp_dir / ".claude").mkdir()
        (temp_dir / ".claude" / "agents").mkdir()
        (temp_dir / ".claude" / "hooks").mkdir()
        (temp_dir / "examples").mkdir()
        (temp_dir / "docs").mkdir()
        
        # Create minimal agent
        agent_content = """---
name: test-agent
description: Test agent for testing
model: sonnet
---

# Role
Test agent for testing purposes.

# Core Competencies
- Testing functionality
- Mock responses

# Standard Operating Procedure
1. Receive input
2. Process input
3. Return result

# Output Format
Basic text output.

# Constraints
- Test environment only
"""
        (temp_dir / ".claude" / "agents" / "test-agent.md").write_text(agent_content)
        
        # Create minimal config
        config = {
            "agents": {
                "test-agent": {
                    "path": "agents/test-agent.md",
                    "description": "Test agent",
                    "model": "sonnet"
                }
            }
        }
        (temp_dir / ".claude" / "config.json").write_text(json.dumps(config, indent=2))
        
        # Create minimal hook
        hook_content = '''#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.loads(sys.stdin.read())
    result = {"status": "allow", "messages": [], "warnings": []}
    print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "messages": [str(e)], "warnings": []}
    print(json.dumps(result))
'''
        hook_path = temp_dir / ".claude" / "hooks" / "test_validator.py"
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)
        
        return temp_dir
    
    @staticmethod
    def cleanup_temp_project(temp_dir: Path):
        """Clean up temporary project directory"""
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @staticmethod
    def create_mock_claude_client() -> Mock:
        """Create a mock Claude client for testing"""
        mock_client = Mock()
        mock_client.messages = Mock()
        mock_client.messages.create = AsyncMock()
        
        # Default response
        mock_response = Mock()
        mock_response.content = [Mock(text="Mock response")]
        mock_client.messages.create.return_value = mock_response
        
        return mock_client
    
    @staticmethod
    def create_sample_mcp_server_content() -> str:
        """Create sample MCP server content for testing"""
        return """
from fastmcp import FastMCP
from pydantic import BaseModel
import asyncio

mcp = FastMCP("test-server")

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

@mcp.tool
async def search(request: SearchRequest):
    \"\"\"Search for items\"\"\"
    return {
        "results": [f"Result {i} for {request.query}" for i in range(request.limit)],
        "total": request.limit
    }

@mcp.tool
async def health_check():
    \"\"\"Check server health\"\"\"
    return {"status": "healthy", "timestamp": "2025-01-09T00:00:00Z"}

if __name__ == "__main__":
    asyncio.run(mcp.run())
"""
    
    @staticmethod
    def assert_json_response(response_str: str) -> Dict[str, Any]:
        """Assert response is valid JSON and return parsed data"""
        try:
            data = json.loads(response_str)
            assert isinstance(data, dict), "Response should be a JSON object"
            return data
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}")
    
    @staticmethod
    def assert_security_response(response: Dict[str, Any], expected_status: str):
        """Assert security hook response has expected format and status"""
        required_fields = ["status", "messages", "warnings"]
        for field in required_fields:
            assert field in response, f"Security response missing field: {field}"
        
        assert response["status"] == expected_status, \
            f"Expected status {expected_status}, got {response['status']}"
        
        assert isinstance(response["messages"], list), "Messages should be a list"
        assert isinstance(response["warnings"], list), "Warnings should be a list"
    
    @staticmethod
    async def run_async_test(coro):
        """Run async test function"""
        return await coro
    
    @staticmethod
    def capture_subprocess_output(cmd: List[str], input_data: str = "", cwd: Optional[Path] = None):
        """Capture subprocess output for testing"""
        import subprocess
        
        result = subprocess.run(
            cmd,
            input=input_data,
            text=True,
            capture_output=True,
            cwd=cwd
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }


class MockClaude:
    """Enhanced mock Claude client with response patterns"""
    
    def __init__(self):
        self.responses = {}
        self.call_history = []
        self.default_response = "Mock response from Claude"
    
    def add_response_pattern(self, pattern: str, response: str):
        """Add a response pattern for specific input"""
        self.responses[pattern.lower()] = response
    
    def add_json_response_pattern(self, pattern: str, response_data: Dict[str, Any]):
        """Add a JSON response pattern"""
        self.responses[pattern.lower()] = json.dumps(response_data)
    
    async def mock_create_message(self, **kwargs):
        """Mock the message creation"""
        # Store call history
        self.call_history.append(kwargs)
        
        # Extract message content
        messages = kwargs.get('messages', [])
        if messages:
            content = messages[-1].get('content', '').lower()
            
            # Find matching response pattern
            for pattern, response in self.responses.items():
                if pattern in content:
                    return Mock(content=[Mock(text=response)])
        
        # Return default response
        return Mock(content=[Mock(text=self.default_response)])
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all calls made"""
        return self.call_history.copy()
    
    def reset(self):
        """Reset mock state"""
        self.call_history = []
        self.responses = {}


class AgentTestHarness:
    """Test harness for comprehensive agent testing"""
    
    def __init__(self, agent_class=None):
        self.agent_class = agent_class
        self.mock_claude = MockClaude()
        self.temp_project = None
    
    def setup_test_environment(self):
        """Set up test environment"""
        self.temp_project = TestUtils.create_temp_project()
        return self.temp_project
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.temp_project:
            TestUtils.cleanup_temp_project(self.temp_project)
    
    async def test_agent_workflow(self, test_messages: List[str]) -> List[Dict[str, Any]]:
        """Test complete agent workflow"""
        if not self.agent_class:
            raise ValueError("Agent class not specified")
        
        agent = self.agent_class()
        results = []
        
        with patch.object(agent, 'client', self.mock_claude):
            await agent.create_conversation()
            
            for message in test_messages:
                try:
                    result = await agent.send_message(message)
                    results.append(result)
                except Exception as e:
                    results.append({"status": "error", "error": str(e)})
        
        return results
    
    def add_agent_response(self, trigger: str, response: str):
        """Add response pattern for agent"""
        self.mock_claude.add_response_pattern(trigger, response)
    
    def add_agent_json_response(self, trigger: str, response_data: Dict[str, Any]):
        """Add JSON response pattern for agent"""
        self.mock_claude.add_json_response_pattern(trigger, response_data)


@pytest.fixture
def temp_project():
    """Fixture for temporary project"""
    temp_dir = TestUtils.create_temp_project()
    yield temp_dir
    TestUtils.cleanup_temp_project(temp_dir)


@pytest.fixture
def mock_anthropic_client():
    """Fixture for mock Anthropic client"""
    return TestUtils.create_mock_claude_client()


@pytest.fixture
def sample_mcp_server():
    """Fixture for sample MCP server content"""
    return TestUtils.create_sample_mcp_server_content()


@pytest.fixture
def agent_test_harness():
    """Fixture for agent test harness"""
    harness = AgentTestHarness()
    yield harness
    harness.cleanup_test_environment()


class TestTestUtils:
    """Test the test utilities themselves"""
    
    def test_create_temp_project(self):
        """Test temp project creation"""
        temp_dir = TestUtils.create_temp_project()
        
        try:
            # Check basic structure exists
            assert temp_dir.exists()
            assert (temp_dir / ".claude").exists()
            assert (temp_dir / ".claude" / "agents").exists()
            assert (temp_dir / ".claude" / "hooks").exists()
            
            # Check files were created
            assert (temp_dir / ".claude" / "config.json").exists()
            assert (temp_dir / ".claude" / "agents" / "test-agent.md").exists()
            assert (temp_dir / ".claude" / "hooks" / "test_validator.py").exists()
            
            # Check content is valid
            config_content = (temp_dir / ".claude" / "config.json").read_text()
            config_data = json.loads(config_content)
            assert "agents" in config_data
            
        finally:
            TestUtils.cleanup_temp_project(temp_dir)
    
    def test_mock_claude_client(self):
        """Test mock Claude client"""
        mock_client = TestUtils.create_mock_claude_client()
        
        assert mock_client is not None
        assert hasattr(mock_client, 'messages')
        assert hasattr(mock_client.messages, 'create')
    
    def test_sample_mcp_server_content(self):
        """Test sample MCP server content"""
        content = TestUtils.create_sample_mcp_server_content()
        
        assert "FastMCP" in content
        assert "@mcp.tool" in content
        assert "async def" in content
        assert "health_check" in content
    
    def test_assert_json_response(self):
        """Test JSON response assertion"""
        valid_json = '{"status": "success", "data": []}'
        result = TestUtils.assert_json_response(valid_json)
        
        assert isinstance(result, dict)
        assert result["status"] == "success"
        
        # Test invalid JSON
        with pytest.raises(Exception):
            TestUtils.assert_json_response("invalid json")
    
    def test_assert_security_response(self):
        """Test security response assertion"""
        valid_response = {
            "status": "allow",
            "messages": [],
            "warnings": ["test warning"]
        }
        
        # Should not raise exception
        TestUtils.assert_security_response(valid_response, "allow")
        
        # Test invalid response
        invalid_response = {"status": "allow"}  # Missing fields
        with pytest.raises(AssertionError):
            TestUtils.assert_security_response(invalid_response, "allow")
    
    def test_capture_subprocess_output(self):
        """Test subprocess output capture"""
        result = TestUtils.capture_subprocess_output(
            [sys.executable, "-c", "print('hello world')"]
        )
        
        assert result["returncode"] == 0
        assert "hello world" in result["stdout"]
        assert isinstance(result["stderr"], str)


class TestMockClaude:
    """Test MockClaude functionality"""
    
    def test_mock_claude_initialization(self):
        """Test MockClaude initializes correctly"""
        mock = MockClaude()
        
        assert mock.responses == {}
        assert mock.call_history == []
        assert mock.default_response == "Mock response from Claude"
    
    def test_add_response_pattern(self):
        """Test adding response patterns"""
        mock = MockClaude()
        mock.add_response_pattern("hello", "Hello back!")
        
        assert "hello" in mock.responses
        assert mock.responses["hello"] == "Hello back!"
    
    def test_add_json_response_pattern(self):
        """Test adding JSON response patterns"""
        mock = MockClaude()
        response_data = {"status": "success", "message": "test"}
        mock.add_json_response_pattern("test", response_data)
        
        assert "test" in mock.responses
        parsed = json.loads(mock.responses["test"])
        assert parsed == response_data
    
    @pytest.mark.asyncio
    async def test_mock_create_message(self):
        """Test mock message creation"""
        mock = MockClaude()
        mock.add_response_pattern("fastmcp", "FastMCP implementation")
        
        # Test pattern matching
        result = await mock.mock_create_message(
            messages=[{"content": "Help me with FastMCP"}]
        )
        
        assert result.content[0].text == "FastMCP implementation"
        
        # Test call history
        assert len(mock.get_call_history()) == 1
    
    @pytest.mark.asyncio
    async def test_default_response(self):
        """Test default response when no pattern matches"""
        mock = MockClaude()
        
        result = await mock.mock_create_message(
            messages=[{"content": "Unknown request"}]
        )
        
        assert result.content[0].text == "Mock response from Claude"
    
    def test_reset_functionality(self):
        """Test reset functionality"""
        mock = MockClaude()
        mock.add_response_pattern("test", "response")
        mock.call_history.append({"test": "data"})
        
        mock.reset()
        
        assert mock.responses == {}
        assert mock.call_history == []


class TestAgentTestHarness:
    """Test AgentTestHarness functionality"""
    
    def test_harness_initialization(self):
        """Test harness initializes correctly"""
        harness = AgentTestHarness()
        
        assert harness.agent_class is None
        assert isinstance(harness.mock_claude, MockClaude)
        assert harness.temp_project is None
    
    def test_setup_test_environment(self):
        """Test test environment setup"""
        harness = AgentTestHarness()
        
        try:
            temp_dir = harness.setup_test_environment()
            
            assert temp_dir.exists()
            assert harness.temp_project == temp_dir
            
        finally:
            harness.cleanup_test_environment()
    
    def test_add_response_patterns(self):
        """Test adding response patterns to harness"""
        harness = AgentTestHarness()
        
        harness.add_agent_response("test", "test response")
        harness.add_agent_json_response("json", {"key": "value"})
        
        assert "test" in harness.mock_claude.responses
        assert "json" in harness.mock_claude.responses


def run_integration_tests():
    """Run integration tests using test utilities"""
    test_suite = [
        "tests/test_integration.py",
        "tests/test_performance.py",
        "claude_code_sdk/test/test_claude_integration.py",
        "claude_code_sdk/test/test_rate_limiter.py",
        "claude_code_sdk/test/test_cli.py",
        "claude_code_sdk/test/test_security.py",
        "claude_code_sdk/test/test_agents.py",
        __file__
    ]
    
    return pytest.main(["-v", "--tb=short"] + test_suite)


def run_performance_benchmarks():
    """Run performance benchmarks"""
    return pytest.main([
        "tests/test_performance.py",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "-v"
    ])


def run_security_tests():
    """Run security-focused tests"""
    return pytest.main([
        "claude_code_sdk/test/test_security.py",
        "tests/test_integration.py::TestSecuritySystem",
        "-v",
        "--tb=short"
    ])


if __name__ == "__main__":
    # Run all test utilities tests
    pytest.main([__file__, "-v", "--tb=short"])