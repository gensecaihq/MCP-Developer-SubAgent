# MCP Protocol Debugging Guide

## Common Issues and Solutions

### 1. Client Not Receiving Tool Responses

**Symptoms:**
- Tools execute but client doesn't receive results
- Timeout errors on client side

**Debugging Steps:**

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add logging to your MCP server
from fastmcp import FastMCP
mcp = FastMCP("debug-server", log_level="DEBUG")
```

### 2. Capability Negotiation Failures

**Check capability exchange:**
```python
@mcp.startup()
async def log_capabilities():
    print(f"Server capabilities: {mcp.capabilities}")
```

### 3. Message Format Issues

**Validate JSON-RPC format:**
```python
import json

@mcp.tool()
async def debug_tool(param: str) -> Dict[str, Any]:
    # Log the incoming request
    print(f"Received param: {json.dumps(param, indent=2)}")
    
    result = {"processed": param}
    
    # Log the outgoing response
    print(f"Sending result: {json.dumps(result, indent=2)}")
    
    return result
```

### 4. Async Execution Problems

**Common async pitfalls:**
```python
# Wrong - forgetting await
@mcp.tool()
async def bad_tool():
    return fetch_data()  # Missing await!

# Correct
@mcp.tool()
async def good_tool():
    return await fetch_data()
```

### 5. Connection Issues

**Test with minimal client:**
```python
import asyncio
import json

async def test_mcp_server():
    reader, writer = await asyncio.open_connection('localhost', 8080)
    
    # Send initialization
    init_msg = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {"capabilities": {}},
        "id": 1
    }
    
    writer.write(json.dumps(init_msg).encode() + b'\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    print(f"Response: {response.decode()}")
```

## Protocol Tracing

Use MCP Inspector or implement custom tracing:

```python
class TracingMCP(FastMCP):
    async def handle_message(self, message: Dict[str, Any]):
        print(f"→ Received: {json.dumps(message, indent=2)}")
        result = await super().handle_message(message)
        print(f"← Sending: {json.dumps(result, indent=2)}")
        return result
```

## Performance Profiling

```python
import time
from functools import wraps

def profile_tool(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper

@mcp.tool()
@profile_tool
async def slow_tool():
    await asyncio.sleep(1)
    return "Done"
```
