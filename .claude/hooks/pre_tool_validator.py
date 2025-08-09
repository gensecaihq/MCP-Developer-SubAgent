#!/usr/bin/env python3
"""
Pre-tool validation hook for Claude Code MCP Development
Validates tool execution before processing
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List


def validate_mcp_tool(tool_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate MCP tool execution before processing
    
    Args:
        tool_data: Tool execution data from Claude Code
    
    Returns:
        Validation result with status and messages
    """
    result = {
        "status": "allow",
        "messages": [],
        "warnings": []
    }
    
    tool_type = tool_data.get("toolType", "")
    file_path = tool_data.get("filePath", "")
    
    # Validate file operations
    if tool_type in ["Write", "Edit"]:
        if not file_path:
            result["status"] = "block"
            result["messages"].append("File path required for write/edit operations")
            return result
        
        path = Path(file_path)
        
        # Security checks
        if ".." in str(path):
            result["status"] = "block"
            result["messages"].append("Path traversal detected")
            return result
        
        # Check for sensitive files
        sensitive_patterns = [
            ".env",
            "credentials",
            "secrets",
            "private_key",
            "password"
        ]
        
        for pattern in sensitive_patterns:
            if pattern in file_path.lower():
                result["status"] = "warn"
                result["warnings"].append(f"Potentially sensitive file: {pattern}")
        
        # Validate Python files
        if path.suffix == ".py":
            # Check for MCP patterns
            content = tool_data.get("content", "")
            if content:
                if "@mcp.tool" in content or "FastMCP" in content:
                    result["messages"].append("MCP server implementation detected")
                    
                    # Validate required imports
                    required_imports = [
                        "from fastmcp import FastMCP",
                        "from pydantic import"
                    ]
                    
                    for import_stmt in required_imports:
                        if import_stmt not in content:
                            result["warnings"].append(f"Missing import: {import_stmt}")
                
                # Check for security issues - enhanced blocking
                dangerous_patterns = [
                    "eval(",
                    "exec(",
                    "os.system(",
                    "__import__",
                    "subprocess.call(",
                    "subprocess.run(",
                    "os.popen(",
                    "commands.getoutput(",
                    "getattr("
                ]
                
                # Critical patterns that should be blocked, not just warned
                critical_patterns = [
                    "os.system(",
                    "eval(",
                    "exec(",
                    "__import__"
                ]
                
                for pattern in dangerous_patterns:
                    if pattern in content:
                        if pattern in critical_patterns:
                            result["status"] = "block"
                            result["messages"].append(f"Dangerous code pattern blocked: {pattern}")
                            return result
                        else:
                            result["status"] = "warn"
                            result["warnings"].append(f"Security concern: {pattern}")
    
    # Validate command execution
    elif tool_type == "Bash":
        command = tool_data.get("command", "")
        
        # Block empty commands - security fix
        if not command or command.strip() == "":
            result["status"] = "block"
            result["messages"].append("Empty bash commands not allowed")
            return result
        
        # Block dangerous commands
        dangerous_commands = [
            "rm -rf /",
            ":(){ :|:& };:",
            "dd if=/dev/zero",
            "mkfs",
            "format"
        ]
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                result["status"] = "block"
                result["messages"].append(f"Dangerous command blocked: {dangerous}")
                return result
        
        # Warn about sudo
        if "sudo" in command:
            result["status"] = "warn"
            result["warnings"].append("Sudo command requires elevated privileges")
    
    return result


def main():
    """Main hook entry point"""
    try:
        # Read tool data from stdin
        tool_data_json = sys.stdin.read()
        tool_data = json.loads(tool_data_json)
        
        # Validate the tool execution
        validation_result = validate_mcp_tool(tool_data)
        
        # Output result
        print(json.dumps(validation_result))
        
        # Exit with appropriate code
        if validation_result["status"] == "block":
            sys.exit(1)
        elif validation_result["status"] == "warn":
            # Log warnings but allow execution
            for warning in validation_result["warnings"]:
                print(f"WARNING: {warning}", file=sys.stderr)
            sys.exit(0)
        else:
            sys.exit(0)
            
    except Exception as e:
        error_result = {
            "status": "error",
            "messages": [f"Hook error: {str(e)}"]
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()