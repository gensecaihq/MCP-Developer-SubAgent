"""
Comprehensive test module for claude_code_sdk

This module provides comprehensive testing utilities and test cases
for all components of the Claude Code MCP SDK.
"""

from .test_claude_integration import *
from .test_rate_limiter import *
from .test_cli import *
from .test_security import *
from .test_agents import *
from .test_utils import *

__version__ = "1.0.0"
__all__ = [
    # Test utilities
    "TestUtils",
    "MockClaude",
    "AgentTestHarness",
    
    # Test fixtures
    "temp_project",
    "mock_anthropic_client",
    "sample_mcp_server",
    
    # Test runners
    "run_integration_tests",
    "run_performance_benchmarks",
    "run_security_tests",
]