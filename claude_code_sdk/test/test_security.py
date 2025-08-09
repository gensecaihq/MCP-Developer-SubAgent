#!/usr/bin/env python3
"""
Comprehensive security tests for MCP Developer SubAgent System
"""

import pytest
import subprocess
import json
import sys
import tempfile
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSecurityHooks:
    """Test security hooks functionality"""
    
    @pytest.fixture
    def project_root(self):
        """Project root directory"""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def hook_path(self, project_root):
        """Path to security hook"""
        return project_root / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def test_hook_exists(self, hook_path):
        """Test security hook file exists"""
        assert hook_path.exists(), "Security hook file missing"
        assert hook_path.is_file(), "Security hook is not a file"
    
    def test_hook_executable(self, hook_path):
        """Test security hook is executable"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input='{"toolType": "Write", "filePath": "test.py"}', 
           text=True, capture_output=True)
        
        # Should execute without Python syntax errors
        assert result.returncode == 0 or result.stdout, "Hook failed to execute"


class TestSafeCodeValidation:
    """Test validation of safe code patterns"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def _run_hook(self, hook_path, test_input):
        """Helper to run security hook"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        if result.returncode != 0:
            return {"status": "error", "messages": [result.stderr]}
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "error", "messages": ["Invalid JSON response"]}
    
    def test_simple_print_statement(self, hook_path):
        """Test simple print statement is allowed"""
        test_input = {
            "toolType": "Write",
            "filePath": "hello.py",
            "content": "print('Hello, World!')"
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"
    
    def test_basic_imports(self, hook_path):
        """Test basic imports are allowed"""
        test_input = {
            "toolType": "Write",
            "filePath": "imports.py",
            "content": """
import json
import os
from pathlib import Path
import asyncio
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"
    
    def test_function_definitions(self, hook_path):
        """Test function definitions are allowed"""
        test_input = {
            "toolType": "Write",
            "filePath": "functions.py",
            "content": """
def my_function(x, y):
    return x + y

async def async_function():
    return "hello"

class MyClass:
    def __init__(self):
        self.value = 42
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"
    
    def test_fastmcp_patterns(self, hook_path):
        """Test FastMCP patterns are allowed"""
        test_input = {
            "toolType": "Write",
            "filePath": "mcp_server.py",
            "content": """
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("my-server")

@mcp.tool
async def search(query: str):
    return {"results": []}

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"
    
    def test_json_operations(self, hook_path):
        """Test JSON operations are allowed"""
        test_input = {
            "toolType": "Write",
            "filePath": "json_ops.py",
            "content": """
import json

data = {"key": "value"}
json_string = json.dumps(data)
parsed_data = json.loads(json_string)
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"


class TestDangerousCodeBlocking:
    """Test blocking of dangerous code patterns"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def _run_hook(self, hook_path, test_input):
        """Helper to run security hook"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        if result.returncode != 0:
            return {"status": "error", "messages": [result.stderr]}
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "error", "messages": ["Invalid JSON response"]}
    
    def test_os_system_blocked(self, hook_path):
        """Test os.system() calls are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "dangerous.py",
            "content": """
import os
os.system('rm -rf /')
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_eval_blocked(self, hook_path):
        """Test eval() calls are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "eval_danger.py",
            "content": """
user_input = "malicious code"
eval(user_input)
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_exec_blocked(self, hook_path):
        """Test exec() calls are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "exec_danger.py",
            "content": """
malicious_code = "import os; os.system('bad')"
exec(malicious_code)
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_import_injection_blocked(self, hook_path):
        """Test __import__ injection is blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "import_injection.py", 
            "content": """
module = __import__('os')
module.system('dangerous command')
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_subprocess_dangerous_blocked(self, hook_path):
        """Test dangerous subprocess calls are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "subprocess_danger.py",
            "content": """
import subprocess
subprocess.call(['rm', '-rf', '/'])
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_multiple_patterns_blocked(self, hook_path):
        """Test multiple dangerous patterns are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "multi_danger.py",
            "content": """
import os
import subprocess

# Multiple dangerous patterns
os.system('bad command')
eval('malicious code')
exec('more malicious code')
subprocess.call(['dangerous', 'command'])
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"


class TestEmptyCommandBlocking:
    """Test blocking of empty bash commands"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def _run_hook(self, hook_path, test_input):
        """Helper to run security hook"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "error", "messages": ["Invalid JSON response"]}
    
    def test_empty_bash_command_blocked(self, hook_path):
        """Test empty bash commands are blocked"""
        test_input = {
            "toolType": "Bash",
            "command": ""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_whitespace_only_command_blocked(self, hook_path):
        """Test whitespace-only commands are blocked"""
        test_input = {
            "toolType": "Bash",
            "command": "   \n\t   "
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_valid_bash_command_allowed(self, hook_path):
        """Test valid bash commands are allowed"""
        test_input = {
            "toolType": "Bash",
            "command": "echo 'hello world'"
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "allow"


class TestInputValidation:
    """Test input validation and error handling"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def test_invalid_json_input(self, hook_path):
        """Test handling of invalid JSON input"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input='invalid json', text=True, capture_output=True)
        
        # Should handle gracefully
        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["status"] == "error"
    
    def test_missing_required_fields(self, hook_path):
        """Test handling of missing required fields"""
        test_input = {
            "filePath": "test.py"
            # Missing toolType
        }
        
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        response = json.loads(result.stdout)
        assert response["status"] in ["error", "allow"]  # Should handle gracefully
    
    def test_unknown_tool_type(self, hook_path):
        """Test handling of unknown tool types"""
        test_input = {
            "toolType": "UnknownTool",
            "data": "some data"
        }
        
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        response = json.loads(result.stdout)
        # Should handle gracefully (allow unknown types or error appropriately)
        assert response["status"] in ["allow", "error"]
    
    def test_very_large_input(self, hook_path):
        """Test handling of very large input"""
        large_content = "print('hello')\n" * 10000  # Large but safe content
        
        test_input = {
            "toolType": "Write",
            "filePath": "large.py",
            "content": large_content
        }
        
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        # Should handle large inputs
        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["status"] in ["allow", "block"]


class TestSecurityEdgeCases:
    """Test security edge cases and bypass attempts"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def _run_hook(self, hook_path, test_input):
        """Helper to run security hook"""
        result = subprocess.run([
            sys.executable, str(hook_path)
        ], input=json.dumps(test_input), text=True, capture_output=True)
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "error", "messages": ["Invalid JSON response"]}
    
    def test_obfuscated_os_system(self, hook_path):
        """Test obfuscated os.system calls are blocked"""
        test_input = {
            "toolType": "Write",
            "filePath": "obfuscated.py",
            "content": """
import os
getattr(os, 'system')('dangerous command')
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        # Should be blocked or at least warned
        assert result["status"] in ["block", "warn"]
    
    def test_dynamic_import_bypass_attempt(self, hook_path):
        """Test dynamic import bypass attempts"""
        test_input = {
            "toolType": "Write",
            "filePath": "dynamic_import.py",
            "content": """
module_name = 'os'
os_module = __import__(module_name)
os_module.system('bad command')
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        assert result["status"] == "block"
    
    def test_base64_encoded_payload(self, hook_path):
        """Test base64 encoded dangerous payload"""
        import base64
        
        # Encode a dangerous command
        dangerous_code = "import os; os.system('rm -rf /')"
        encoded = base64.b64encode(dangerous_code.encode()).decode()
        
        test_input = {
            "toolType": "Write",
            "filePath": "encoded.py",
            "content": f"""
import base64
code = base64.b64decode('{encoded}').decode()
exec(code)
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        # Should detect exec pattern at minimum
        assert result["status"] == "block"
    
    def test_comment_hiding_attempt(self, hook_path):
        """Test attempts to hide dangerous code in comments"""
        test_input = {
            "toolType": "Write",
            "filePath": "commented.py",
            "content": """
# This looks innocent
print("Hello")

# But hidden dangerous code follows
"""
os.system('dangerous')
"""
"""
        }
        
        result = self._run_hook(hook_path, test_input)
        # Should still detect the dangerous pattern
        assert result["status"] == "block"


class TestPerformanceAndReliability:
    """Test security hook performance and reliability"""
    
    @pytest.fixture
    def hook_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "hooks" / "pre_tool_validator.py"
    
    def test_hook_performance(self, hook_path):
        """Test security hook performance"""
        import time
        
        test_input = {
            "toolType": "Write",
            "filePath": "perf_test.py",
            "content": "print('performance test')"
        }
        
        # Run multiple times to test performance
        times = []
        for _ in range(10):
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, str(hook_path)
            ], input=json.dumps(test_input), text=True, capture_output=True)
            
            end_time = time.time()
            times.append(end_time - start_time)
            
            # Should complete successfully
            assert result.returncode == 0
        
        avg_time = sum(times) / len(times)
        # Should be fast (under 1 second average)
        assert avg_time < 1.0, f"Security hook too slow: {avg_time:.3f}s average"
    
    def test_concurrent_hook_execution(self, hook_path):
        """Test concurrent execution of security hooks"""
        import threading
        import time
        
        results = []
        errors = []
        
        def run_hook():
            try:
                test_input = {
                    "toolType": "Write",
                    "filePath": f"concurrent_{threading.current_thread().ident}.py",
                    "content": "print('concurrent test')"
                }
                
                result = subprocess.run([
                    sys.executable, str(hook_path)
                ], input=json.dumps(test_input), text=True, capture_output=True)
                
                response = json.loads(result.stdout)
                results.append(response)
            except Exception as e:
                errors.append(str(e))
        
        # Run multiple concurrent executions
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_hook)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        # Should complete all executions successfully
        assert len(errors) == 0, f"Errors in concurrent execution: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # All should be allowed (safe code)
        for result in results:
            assert result["status"] == "allow"


def run_security_tests():
    """Run all security tests"""
    return pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_security_tests()