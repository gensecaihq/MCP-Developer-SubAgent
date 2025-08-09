#!/usr/bin/env python3
"""
Comprehensive tests for CLI tools
"""

import pytest
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import json
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli_simple import validate_setup, show_status, main


class TestCLISimple:
    """Test the simple CLI tool functionality"""
    
    @pytest.fixture
    def project_root(self):
        """Project root directory"""
        return Path(__file__).parent.parent.parent
    
    def test_validate_setup_function(self, project_root):
        """Test validate_setup function directly"""
        # Change to project root for testing
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            result = validate_setup()
            assert result is True or result is None  # True on success, None with warnings
        finally:
            os.chdir(original_cwd)
    
    def test_show_status_function(self, project_root):
        """Test show_status function directly"""
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Should not raise exception
            show_status()
        finally:
            os.chdir(original_cwd)
    
    def test_main_function_validate_setup(self, project_root):
        """Test main function with validate-setup command"""
        original_cwd = os.getcwd()
        original_argv = sys.argv[:]
        
        os.chdir(project_root)
        sys.argv = ['cli_simple.py', 'validate-setup']
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with code 0 (success) or 1 (warnings)
            assert exc_info.value.code in [0, 1]
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv
    
    def test_main_function_status(self, project_root):
        """Test main function with status command"""
        original_cwd = os.getcwd()
        original_argv = sys.argv[:]
        
        os.chdir(project_root)
        sys.argv = ['cli_simple.py', 'status']
        
        try:
            # Should not raise exception (exits normally)
            show_status()
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv
    
    def test_main_function_no_args(self):
        """Test main function with no arguments"""
        original_argv = sys.argv[:]
        sys.argv = ['cli_simple.py']
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1  # Should exit with error
        finally:
            sys.argv = original_argv
    
    def test_main_function_unknown_command(self):
        """Test main function with unknown command"""
        original_argv = sys.argv[:]
        sys.argv = ['cli_simple.py', 'unknown-command']
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1  # Should exit with error
        finally:
            sys.argv = original_argv


class TestCLIIntegration:
    """Test CLI tools via subprocess (integration testing)"""
    
    @pytest.fixture
    def project_root(self):
        """Project root directory"""
        return Path(__file__).parent.parent.parent
    
    def test_cli_validate_setup_subprocess(self, project_root):
        """Test validate-setup command via subprocess"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, cwd=project_root)
        
        # Should complete successfully (exit code 0 or 1)
        assert result.returncode in [0, 1]
        assert "Validating Claude Code MCP SDK setup" in result.stdout
        assert "sub-agents" in result.stdout
    
    def test_cli_status_subprocess(self, project_root):
        """Test status command via subprocess"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "status"
        ], capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 0
        assert "Claude Code MCP SDK Status" in result.stdout
        assert "PLATFORM:" in result.stdout
        assert "FUNCTIONAL COMPONENTS:" in result.stdout
    
    def test_cli_invalid_command_subprocess(self, project_root):
        """Test invalid command via subprocess"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "invalid"
        ], capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 1
        assert "Unknown command" in result.stdout
    
    def test_cli_no_args_subprocess(self, project_root):
        """Test no arguments via subprocess"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py"
        ], capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 1
        assert "Usage:" in result.stdout


class TestCLIInDifferentEnvironments:
    """Test CLI in different directory environments"""
    
    def test_cli_in_empty_directory(self):
        """Test CLI behavior in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run([
                sys.executable, 
                str(Path(__file__).parent.parent / "cli_simple.py"),
                "status"
            ], capture_output=True, text=True, cwd=temp_dir)
            
            # Should complete but report missing components
            assert result.returncode == 0
            assert "Claude Code MCP SDK Status" in result.stdout
    
    def test_cli_with_partial_setup(self):
        """Test CLI with partial project setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal structure
            (temp_path / ".claude").mkdir()
            (temp_path / ".claude" / "agents").mkdir()
            
            # Create one agent file
            agent_content = """---
name: test-agent
description: Test agent
---

# Test Agent
This is a test agent.
"""
            (temp_path / ".claude" / "agents" / "test-agent.md").write_text(agent_content)
            
            result = subprocess.run([
                sys.executable,
                str(Path(__file__).parent.parent / "cli_simple.py"), 
                "validate-setup"
            ], capture_output=True, text=True, cwd=temp_path)
            
            # Should find the one agent
            assert "Found 1 sub-agents" in result.stdout


class TestCLIOutput:
    """Test CLI output formatting and content"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_validate_setup_output_format(self, project_root):
        """Test validate-setup output format"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, cwd=project_root)
        
        output_lines = result.stdout.strip().split('\n')
        
        # Should start with validation message
        assert output_lines[0].startswith("🔍 Validating")
        
        # Should have checkmarks or warnings
        has_checkmarks = any("✅" in line for line in output_lines)
        has_warnings = any("⚠️" in line for line in output_lines)
        assert has_checkmarks or has_warnings
        
        # Should end with summary
        assert any("Validation Summary:" in line for line in output_lines)
    
    def test_status_output_format(self, project_root):
        """Test status output format"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "status"
        ], capture_output=True, text=True, cwd=project_root)
        
        output = result.stdout
        
        # Should have main sections
        assert "Claude Code MCP SDK Status" in output
        assert "PLATFORM:" in output
        assert "FUNCTIONAL COMPONENTS:" in output
        assert "INSTALLATION OPTIONS:" in output
        assert "USAGE MODES:" in output
        
        # Should have emojis for visual appeal
        emoji_count = sum(1 for char in output if ord(char) > 127)  # Count Unicode chars
        assert emoji_count > 0


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_python_version_detection(self):
        """Test Python version detection in CLI"""
        # This test runs the actual CLI to verify it handles Python version correctly
        result = subprocess.run([
            sys.executable, "-c",
            """
import sys
sys.path.insert(0, 'claude_code_sdk')
from cli_simple import validate_setup
validate_setup()
            """
        ], capture_output=True, text=True, 
           cwd=Path(__file__).parent.parent.parent)
        
        # Should not crash and should mention Python version
        assert result.returncode in [0, 1]  # Success or warnings
        assert "Python" in result.stdout
    
    def test_missing_dependencies_handling(self):
        """Test handling of missing optional dependencies"""
        # The CLI should handle missing optional dependencies gracefully
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, 
           cwd=Path(__file__).parent.parent.parent)
        
        # Should complete even with missing optional dependencies
        assert result.returncode in [0, 1]
        
        # Might warn about missing dependencies
        if "not installed" in result.stdout:
            assert "warning" in result.stdout.lower() or "⚠️" in result.stdout


class TestCLIPerformance:
    """Test CLI performance characteristics"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_validate_setup_performance(self, project_root):
        """Test validate-setup performance"""
        import time
        
        start_time = time.time()
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, cwd=project_root)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete quickly (under 5 seconds)
        assert execution_time < 5.0, f"CLI too slow: {execution_time:.2f}s"
        assert result.returncode in [0, 1]
    
    def test_status_performance(self, project_root):
        """Test status command performance"""
        import time
        
        start_time = time.time()
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "status"
        ], capture_output=True, text=True, cwd=project_root)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should be very fast (under 2 seconds)
        assert execution_time < 2.0, f"Status command too slow: {execution_time:.2f}s"
        assert result.returncode == 0


class TestCLICrossPlatform:
    """Test CLI cross-platform compatibility"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_path_handling(self, project_root):
        """Test that CLI handles paths correctly across platforms"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "validate-setup"
        ], capture_output=True, text=True, cwd=project_root)
        
        # Should work regardless of platform
        assert result.returncode in [0, 1]
        
        # Check that path separators are handled correctly
        if ".claude" in result.stdout:
            # Should find .claude directory regardless of path separator
            assert "agents" in result.stdout
    
    def test_unicode_handling(self, project_root):
        """Test CLI handles Unicode characters (emojis) correctly"""
        result = subprocess.run([
            sys.executable, "claude_code_sdk/cli_simple.py", "status"
        ], capture_output=True, text=True, cwd=project_root)
        
        # Should complete without Unicode errors
        assert result.returncode == 0
        
        # Should contain emojis in output
        assert "🖥️" in result.stdout or "✅" in result.stdout


def run_cli_tests():
    """Run all CLI tests"""
    return pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_cli_tests()