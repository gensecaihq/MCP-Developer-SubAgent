"""
Basic MCP Server Example
Demonstrates fundamental MCP server patterns using FastMCP
"""

from fastmcp import FastMCP, Tool
from typing import Dict, Any
import asyncio

# Initialize MCP server
mcp = FastMCP("basic-example-server", version="1.0.0")

@mcp.tool()
async def greet(name: str) -> str:
    """
    Simple greeting tool
    
    Args:
        name: The name to greet
        
    Returns:
        A personalized greeting message
    """
    return f"Hello, {name}! Welcome to MCP development."

@mcp.tool()
async def calculate(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform basic calculations
    
    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        a: First number
        b: Second number
        
    Returns:
        Dictionary with operation and result
    """
    operations = {
        'add': a + b,
        'subtract': a - b,
        'multiply': a * b,
        'divide': a / b if b != 0 else None
    }
    
    result = operations.get(operation)
    if result is None and operation == 'divide' and b == 0:
        return {"error": "Division by zero"}
    elif result is None:
        return {"error": f"Unknown operation: {operation}"}
    
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result
    }

if __name__ == "__main__":
    # Run the server
    asyncio.run(mcp.run())
