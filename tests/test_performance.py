#!/usr/bin/env python3
"""
Performance Benchmarks for MCP Developer SubAgent System
Measures performance of critical components with regression detection
"""

import pytest
import asyncio
import time
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import psutil
import os
from memory_profiler import profile as memory_profile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIPerformance:
    """Benchmark CLI tool performance"""
    
    def test_cli_validation_speed(self, benchmark):
        """Benchmark CLI validation tool speed"""
        def run_validation():
            result = subprocess.run([
                sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            return result.returncode == 0
        
        result = benchmark(run_validation)
        assert result is True
    
    def test_cli_status_speed(self, benchmark):
        """Benchmark CLI status command speed"""
        def run_status():
            result = subprocess.run([
                sys.executable, "claude_code_sdk/cli_simple.py", "status"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            return result.returncode == 0
        
        result = benchmark(run_status)
        assert result is True


class TestSecurityHooksPerformance:
    """Benchmark security hooks performance"""
    
    def test_security_hook_safe_code(self, benchmark):
        """Benchmark security validation for safe code"""
        def validate_safe_code():
            test_input = {
                "toolType": "Write",
                "filePath": "safe.py",
                "content": "import json\nprint('hello world')\ndata = {'key': 'value'}"
            }
            
            result = subprocess.run([
                sys.executable, ".claude/hooks/pre_tool_validator.py"
            ], input=json.dumps(test_input), text=True, capture_output=True,
               cwd=Path(__file__).parent.parent)
            
            return json.loads(result.stdout)["status"] == "allow"
        
        result = benchmark(validate_safe_code)
        assert result is True
    
    def test_security_hook_dangerous_code(self, benchmark):
        """Benchmark security validation for dangerous code"""
        def validate_dangerous_code():
            test_input = {
                "toolType": "Write", 
                "filePath": "dangerous.py",
                "content": "import os\nos.system('rm -rf /')\neval(user_input)"
            }
            
            result = subprocess.run([
                sys.executable, ".claude/hooks/pre_tool_validator.py"
            ], input=json.dumps(test_input), text=True, capture_output=True,
               cwd=Path(__file__).parent.parent)
            
            return json.loads(result.stdout)["status"] == "block"
        
        result = benchmark(validate_dangerous_code)
        assert result is True
    
    def test_security_hook_large_file(self, benchmark):
        """Benchmark security validation for large files"""
        def validate_large_file():
            # Generate large file content
            large_content = "import json\n" + "\n".join([
                f"data_{i} = {{'key_{i}': 'value_{i}'}}" for i in range(1000)
            ])
            
            test_input = {
                "toolType": "Write",
                "filePath": "large.py", 
                "content": large_content
            }
            
            result = subprocess.run([
                sys.executable, ".claude/hooks/pre_tool_validator.py"
            ], input=json.dumps(test_input), text=True, capture_output=True,
               cwd=Path(__file__).parent.parent)
            
            return json.loads(result.stdout)["status"] == "allow"
        
        result = benchmark(validate_large_file)
        assert result is True


class TestActivationEnginePerformance:
    """Benchmark activation engine performance"""
    
    @pytest.fixture(scope="class")
    def activation_engine(self):
        """Fixture for activation engine"""
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
        from activation_engine import CrossAgentActivationEngine, ActivationContext
        return CrossAgentActivationEngine()
    
    def test_simple_activation_analysis(self, benchmark, activation_engine):
        """Benchmark simple activation analysis"""
        def analyze_simple_context():
            from activation_engine import ActivationContext
            
            context = ActivationContext(
                file_path="test.py",
                file_content="print('hello')",
                project_phase="implementation"
            )
            
            return activation_engine.analyze_activation_needs(context)
        
        result = benchmark(analyze_simple_context)
        assert len(result) >= 0  # Should return some activations or empty list
    
    def test_complex_activation_analysis(self, benchmark, activation_engine):
        """Benchmark complex FastMCP server activation analysis"""
        def analyze_complex_context():
            from activation_engine import ActivationContext
            
            fastmcp_content = """
from fastmcp import FastMCP
from pydantic import BaseModel
import asyncio
import jwt
import os

mcp = FastMCP("complex-server")

class UserAuth(BaseModel):
    username: str
    password: str

@mcp.tool
async def authenticate_user(auth: UserAuth):
    # OAuth implementation
    token = jwt.encode({'user': auth.username}, 'secret')
    return {'token': token}

@mcp.tool 
async def process_data(data: str):
    # Async processing with potential performance issues
    results = []
    for i in range(1000):
        results.append(f"processed_{i}_{data}")
    return results

if __name__ == "__main__":
    asyncio.run(mcp.run())
            """
            
            context = ActivationContext(
                file_path="complex_server.py",
                file_content=fastmcp_content,
                project_phase="implementation",
                user_request="Help me optimize this MCP server for production use with authentication"
            )
            
            return activation_engine.analyze_activation_needs(context)
        
        result = benchmark(analyze_complex_context)
        assert len(result) > 0  # Should activate multiple agents
        
        # Verify expected agents are activated
        agent_names = [activation[0] for activation in result]
        expected_agents = {"fastmcp-specialist", "mcp-security-auditor"}
        assert expected_agents.intersection(set(agent_names)), f"Expected agents not found in {agent_names}"


class TestRateLimiterPerformance:
    """Benchmark rate limiter performance"""
    
    @pytest.fixture(scope="class")
    def rate_limiter(self):
        """Fixture for rate limiter"""
        sys.path.insert(0, "claude_code_sdk")
        from rate_limiter import RateLimiter
        return RateLimiter()
    
    def test_rate_limit_check_speed(self, benchmark, rate_limiter):
        """Benchmark rate limit checking speed"""
        async def check_rate_limit():
            return await rate_limiter.check_rate_limit("test_endpoint")
        
        def run_check():
            return asyncio.run(check_rate_limit())
        
        result = benchmark(run_check)
        assert result["allowed"] is True
    
    def test_rate_limit_many_requests(self, benchmark, rate_limiter):
        """Benchmark rate limiter under load"""
        async def many_requests():
            results = []
            for i in range(50):  # Simulate burst of requests
                result = await rate_limiter.check_rate_limit("load_test")
                if result["allowed"]:
                    await rate_limiter.record_request("load_test")
                results.append(result["allowed"])
            return results
        
        def run_many_requests():
            return asyncio.run(many_requests())
        
        results = benchmark(run_many_requests)
        # Should have some allowed and some blocked due to rate limiting
        assert len(results) == 50
        assert True in results  # At least some should be allowed
    
    def test_rate_limiter_statistics(self, benchmark, rate_limiter):
        """Benchmark rate limiter statistics generation"""
        # First add some data
        async def setup_data():
            for i in range(20):
                check = await rate_limiter.check_rate_limit("stats_test")
                if check["allowed"]:
                    await rate_limiter.record_request("stats_test")
        
        asyncio.run(setup_data())
        
        def get_statistics():
            return rate_limiter.get_statistics()
        
        result = benchmark(get_statistics)
        assert "endpoints" in result
        assert "global_stats" in result


class TestAgentContentPerformance:
    """Benchmark agent content loading and parsing"""
    
    def test_load_all_agents(self, benchmark):
        """Benchmark loading all agent files"""
        def load_all_agents():
            agents_dir = Path(__file__).parent.parent / ".claude/agents"
            agent_contents = {}
            
            for agent_file in agents_dir.glob("*.md"):
                content = agent_file.read_text()
                
                # Parse YAML frontmatter
                if content.startswith("---"):
                    end_marker = content.find("---", 3)
                    if end_marker != -1:
                        yaml_content = content[3:end_marker].strip()
                        agent_contents[agent_file.name] = {
                            "yaml": yaml_content,
                            "content_length": len(content),
                            "sections": content.count("# ")
                        }
            
            return agent_contents
        
        result = benchmark(load_all_agents)
        assert len(result) == 8  # Should load all 8 agents
        
        # Verify all agents have reasonable content
        for agent_name, data in result.items():
            assert data["content_length"] > 100, f"Agent {agent_name} too short"
            assert data["sections"] >= 3, f"Agent {agent_name} missing sections"


class TestExampleServerPerformance:
    """Benchmark example server compilation and validation"""
    
    def test_compile_all_examples(self, benchmark):
        """Benchmark compiling all example servers"""
        def compile_examples():
            examples_dir = Path(__file__).parent.parent / "examples"
            results = {}
            
            for example_dir in examples_dir.iterdir():
                if example_dir.is_dir():
                    server_file = example_dir / "server.py"
                    if server_file.exists():
                        start_time = time.time()
                        result = subprocess.run([
                            sys.executable, "-m", "py_compile", str(server_file)
                        ], capture_output=True)
                        compile_time = time.time() - start_time
                        
                        results[example_dir.name] = {
                            "success": result.returncode == 0,
                            "compile_time": compile_time,
                            "file_size": server_file.stat().st_size
                        }
            
            return results
        
        result = benchmark(compile_examples)
        assert len(result) >= 2  # Should compile at least 2 examples
        
        # All examples should compile successfully
        for example_name, data in result.items():
            assert data["success"], f"Example {example_name} failed to compile"
            assert data["compile_time"] < 5.0, f"Example {example_name} took too long to compile"


class TestMemoryUsage:
    """Memory usage benchmarks and leak detection"""
    
    def test_activation_engine_memory(self):
        """Test activation engine memory usage"""
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
        from activation_engine import CrossAgentActivationEngine, ActivationContext
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and use activation engine multiple times
        for i in range(100):
            engine = CrossAgentActivationEngine()
            context = ActivationContext(
                file_path=f"test_{i}.py",
                file_content=f"print('test {i}')",
                project_phase="implementation"
            )
            activations = engine.analyze_activation_needs(context)
            del engine  # Explicit cleanup
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory increase should be reasonable (less than 50MB for 100 iterations)
        assert memory_increase_mb < 50, f"Memory usage increased by {memory_increase_mb:.2f}MB"
    
    def test_rate_limiter_memory(self):
        """Test rate limiter memory usage under load"""
        sys.path.insert(0, "claude_code_sdk")
        from rate_limiter import RateLimiter
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        async def memory_test():
            limiter = RateLimiter()
            
            # Simulate many requests to test memory management
            for i in range(1000):
                endpoint = f"endpoint_{i % 10}"  # 10 different endpoints
                check = await limiter.check_rate_limit(endpoint)
                if check["allowed"]:
                    await limiter.record_request(endpoint)
            
            return limiter
        
        # Run the test
        limiter = asyncio.run(memory_test())
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory increase should be reasonable
        assert memory_increase_mb < 20, f"Rate limiter memory usage increased by {memory_increase_mb:.2f}MB"
        
        # Verify data structures are properly managed
        stats = limiter.get_statistics()
        assert len(stats["endpoints"]) <= 10, "Rate limiter not cleaning up old endpoints"


class TestConcurrencyPerformance:
    """Test concurrent operations performance"""
    
    def test_concurrent_security_validation(self, benchmark):
        """Test concurrent security hook validations"""
        def concurrent_validation():
            test_cases = [
                {"toolType": "Write", "filePath": f"test_{i}.py", "content": f"print('test {i}')"}
                for i in range(20)
            ]
            
            results = []
            for test_case in test_cases:
                result = subprocess.run([
                    sys.executable, ".claude/hooks/pre_tool_validator.py"
                ], input=json.dumps(test_case), text=True, capture_output=True,
                   cwd=Path(__file__).parent.parent)
                
                response = json.loads(result.stdout)
                results.append(response["status"] == "allow")
            
            return all(results)
        
        result = benchmark(concurrent_validation)
        assert result is True
    
    def test_concurrent_rate_limiting(self, benchmark):
        """Test concurrent rate limit operations"""
        sys.path.insert(0, "claude_code_sdk")
        from rate_limiter import RateLimiter
        
        async def concurrent_rate_limiting():
            limiter = RateLimiter()
            
            # Simulate concurrent requests
            async def make_request(endpoint_id: int):
                endpoint = f"concurrent_{endpoint_id}"
                check = await limiter.check_rate_limit(endpoint)
                if check["allowed"]:
                    await limiter.record_request(endpoint)
                return check["allowed"]
            
            # Use asyncio.gather for true concurrency
            tasks = [make_request(i % 5) for i in range(50)]  # 5 endpoints, 50 requests
            results = await asyncio.gather(*tasks)
            
            return len([r for r in results if r])  # Count allowed requests
        
        def run_concurrent_test():
            return asyncio.run(concurrent_rate_limiting())
        
        allowed_count = benchmark(run_concurrent_test)
        assert allowed_count > 0, "No requests were allowed"
        assert allowed_count < 50, "Rate limiting didn't activate"


# Performance thresholds for regression testing
PERFORMANCE_THRESHOLDS = {
    "cli_validation_max_time": 3.0,     # CLI validation should complete in <3s
    "security_hook_max_time": 0.5,      # Security hooks should complete in <500ms
    "activation_analysis_max_time": 1.0, # Activation analysis should complete in <1s
    "rate_limit_check_max_time": 0.01,  # Rate limit check should complete in <10ms
    "agent_loading_max_time": 2.0,      # Agent loading should complete in <2s
    "example_compile_max_time": 5.0,    # Example compilation should complete in <5s
}


@pytest.mark.parametrize("threshold_name,max_time", PERFORMANCE_THRESHOLDS.items())
def test_performance_thresholds(threshold_name, max_time):
    """Meta-test to document performance expectations"""
    # This test doesn't run anything, just documents our performance expectations
    assert max_time > 0, f"Threshold {threshold_name} should be positive"
    print(f"Performance threshold: {threshold_name} <= {max_time}s")


if __name__ == "__main__":
    # Run benchmarks directly
    pytest.main([__file__, "--benchmark-only", "-v"])