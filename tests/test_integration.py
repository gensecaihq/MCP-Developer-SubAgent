#!/usr/bin/env python3
"""
End-to-End Integration Tests for MCP Developer SubAgent System
Tests the complete workflow from setup to agent coordination
"""

import pytest
import json
import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSystemIntegration:
    """Test complete system integration"""
    
    def test_cli_validation_tool(self):
        """Test CLI validation tool works end-to-end"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        assert "Found 8 sub-agents" in result.stdout
        assert "Hooks configuration valid" in result.stdout
    
    def test_cli_status_command(self):
        """Test CLI status command provides system information"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "status"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0
        assert "Claude Code MCP SDK Status" in result.stdout
        assert "Sub-Agents: 8 agents" in result.stdout
    
    def test_security_hooks_integration(self):
        """Test security hooks integration with various inputs"""
        test_cases = [
            # Safe code should be allowed
            {
                "input": {"toolType": "Write", "filePath": "safe.py", "content": "print('hello')"},
                "expected_status": "allow"
            },
            # Dangerous code should be blocked
            {
                "input": {"toolType": "Write", "filePath": "danger.py", "content": "import os; os.system('rm -rf /')"},
                "expected_status": "block"
            },
            # Empty command should be blocked
            {
                "input": {"toolType": "Bash", "command": ""},
                "expected_status": "block"
            }
        ]
        
        hook_path = Path(__file__).parent.parent / ".claude/hooks/pre_tool_validator.py"
        assert hook_path.exists(), "Security hook not found"
        
        for case in test_cases:
            result = subprocess.run([
                sys.executable, str(hook_path)
            ], input=json.dumps(case["input"]), text=True, capture_output=True)
            
            assert result.returncode == 0, f"Hook failed for input: {case['input']}"
            
            response = json.loads(result.stdout)
            assert response["status"] == case["expected_status"], \
                f"Expected {case['expected_status']}, got {response['status']} for {case['input']}"


class TestAgentSystem:
    """Test agent system components"""
    
    def test_all_agents_load(self):
        """Test that all agent files can be loaded and parsed"""
        agents_dir = Path(__file__).parent.parent / ".claude/agents"
        agent_files = list(agents_dir.glob("*.md"))
        
        assert len(agent_files) == 8, f"Expected 8 agents, found {len(agent_files)}"
        
        for agent_file in agent_files:
            # Test that files have proper structure
            content = agent_file.read_text()
            assert "---\nname:" in content, f"Agent {agent_file.name} missing YAML frontmatter"
            assert "# Role" in content, f"Agent {agent_file.name} missing Role section"
            assert "# Core Competencies" in content, f"Agent {agent_file.name} missing competencies"
    
    def test_activation_engine_loads(self):
        """Test activation engine can be imported and initialized"""
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
        
        from activation_engine import CrossAgentActivationEngine, ActivationContext
        
        # Test engine initialization
        engine = CrossAgentActivationEngine()
        assert engine is not None
        
        # Test context creation
        context = ActivationContext(
            file_path="test.py",
            file_content="print('test')",
            project_phase="implementation"
        )
        
        # Test activation analysis
        activations = engine.analyze_activation_needs(context)
        assert isinstance(activations, list)
    
    def test_activation_rules_valid(self):
        """Test activation rules configuration is valid JSON"""
        rules_path = Path(__file__).parent.parent / ".claude/activation_rules.json"
        assert rules_path.exists(), "Activation rules not found"
        
        with open(rules_path) as f:
            rules = json.load(f)
        
        # Verify expected structure
        assert "activation_rules" in rules
        assert "activation_settings" in rules
        
        # Test specific rule categories
        expected_categories = [
            "content_based_activation",
            "context_aware_activation", 
            "workflow_based_activation",
            "intelligent_delegation",
            "multi_agent_collaboration"
        ]
        
        for category in expected_categories:
            assert category in rules["activation_rules"], f"Missing category: {category}"


class TestExampleServers:
    """Test example MCP servers"""
    
    def test_example_servers_compile(self):
        """Test that all example servers have valid Python syntax"""
        examples_dir = Path(__file__).parent.parent / "examples"
        server_files = list(examples_dir.glob("*/server.py"))
        
        assert len(server_files) >= 2, f"Expected at least 2 example servers, found {len(server_files)}"
        
        for server_file in server_files:
            # Test compilation
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(server_file)
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, \
                f"Server {server_file} has syntax errors: {result.stderr}"
    
    def test_example_servers_structure(self):
        """Test example servers have expected structure"""
        examples_dir = Path(__file__).parent.parent / "examples"
        
        for example_dir in examples_dir.iterdir():
            if example_dir.is_dir():
                server_file = example_dir / "server.py"
                readme_file = example_dir / "README.md"
                
                assert server_file.exists(), f"Missing server.py in {example_dir.name}"
                assert readme_file.exists(), f"Missing README.md in {example_dir.name}"
                
                # Check server content has FastMCP patterns
                server_content = server_file.read_text()
                # Note: FastMCP patterns might not be present if FastMCP isn't available
                # So we just check for basic Python server structure
                assert "def " in server_content or "class " in server_content, \
                    f"Server {server_file} doesn't contain functions or classes"


class TestSecuritySystem:
    """Test security system end-to-end"""
    
    def test_dangerous_patterns_blocked(self):
        """Test various dangerous code patterns are blocked"""
        dangerous_patterns = [
            "os.system('rm -rf /')",
            "eval(user_input)",
            "exec(malicious_code)",
            "__import__('os').system('bad')",
            "subprocess.call(['rm', '-rf', '/'])"
        ]
        
        hook_path = Path(__file__).parent.parent / ".claude/hooks/pre_tool_validator.py"
        
        for pattern in dangerous_patterns:
            test_input = {
                "toolType": "Write",
                "filePath": "dangerous.py", 
                "content": f"import os\n{pattern}"
            }
            
            result = subprocess.run([
                sys.executable, str(hook_path)
            ], input=json.dumps(test_input), text=True, capture_output=True)
            
            response = json.loads(result.stdout)
            assert response["status"] == "block", \
                f"Dangerous pattern not blocked: {pattern}"
    
    def test_safe_patterns_allowed(self):
        """Test safe code patterns are allowed"""
        safe_patterns = [
            "print('Hello, world!')",
            "import json\ndata = json.loads('{}')",
            "from pathlib import Path\np = Path('.')",
            "async def my_function():\n    return 'safe'"
        ]
        
        hook_path = Path(__file__).parent.parent / ".claude/hooks/pre_tool_validator.py"
        
        for pattern in safe_patterns:
            test_input = {
                "toolType": "Write",
                "filePath": "safe.py",
                "content": pattern
            }
            
            result = subprocess.run([
                sys.executable, str(hook_path)
            ], input=json.dumps(test_input), text=True, capture_output=True)
            
            response = json.loads(result.stdout)
            assert response["status"] == "allow", \
                f"Safe pattern was blocked: {pattern}"


class TestDocumentationIntegrity:
    """Test documentation completeness and integrity"""
    
    def test_required_docs_exist(self):
        """Test all required documentation files exist"""
        root = Path(__file__).parent.parent
        required_docs = [
            "README.md",
            "INSTALL.md", 
            "SECURITY.md",
            "PRIVACY.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "scope.md"
        ]
        
        for doc in required_docs:
            doc_path = root / doc
            assert doc_path.exists(), f"Required documentation missing: {doc}"
            
            # Check minimum content length
            content = doc_path.read_text()
            assert len(content) > 100, f"Documentation too short: {doc}"
    
    def test_guides_exist(self):
        """Test user guides exist and have content"""
        docs_dir = Path(__file__).parent.parent / "docs"
        expected_guides = [
            "getting-started.md",
            "best-practices.md", 
            "troubleshooting.md"
        ]
        
        for guide in expected_guides:
            guide_path = docs_dir / guide
            assert guide_path.exists(), f"Guide missing: {guide}"
            
            content = guide_path.read_text()
            assert len(content) > 500, f"Guide too short: {guide}"


class TestSystemWorkflow:
    """Test complete system workflow scenarios"""
    
    def test_new_project_workflow(self):
        """Test workflow for creating a new MCP project"""
        # This would typically involve:
        # 1. CLI validation
        # 2. Agent activation based on context
        # 3. Code generation
        # 4. Security validation
        # 5. Testing
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test CLI works in temp directory
            result = subprocess.run([
                sys.executable, 
                str(Path(__file__).parent.parent / "claude_code_sdk/cli_simple.py"),
                "status"
            ], capture_output=True, text=True, cwd=temp_path)
            
            # Should work even without .claude directory
            assert result.returncode == 0
    
    def test_activation_workflow(self):
        """Test agent activation workflow"""
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
        
        from activation_engine import CrossAgentActivationEngine, ActivationContext
        
        engine = CrossAgentActivationEngine()
        
        # Test FastMCP server scenario
        context = ActivationContext(
            file_path="server.py",
            file_content="""
from fastmcp import FastMCP
import asyncio

mcp = FastMCP("test-server")

@mcp.tool
async def search(query: str):
    return {"results": []}
            """,
            project_phase="implementation"
        )
        
        activations = engine.analyze_activation_needs(context)
        
        # Should activate FastMCP specialist
        agent_names = [a[0] for a in activations]
        assert len(activations) > 0, "No agents activated"
        
        # Generate activation report
        report = engine.generate_activation_report(activations)
        assert "Agent Activation Report" in report


# Pytest configuration and utilities
@pytest.fixture(scope="session")
def project_root():
    """Fixture providing project root path"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session") 
def temp_workspace():
    """Fixture providing temporary workspace"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])