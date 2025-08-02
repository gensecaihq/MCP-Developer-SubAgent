# MCP Troubleshooting Guide

## Common Issues

### 1. Server Won't Start

**Error:** `Address already in use`
```bash
# Find process using the port
lsof -i :8080
# Kill the process
kill -9 <PID>
```

**Error:** `Module not found`
```bash
# Ensure dependencies are installed
pip install fastmcp
pip install -r requirements.txt
```

### 2. Client Connection Failures

**Check server is running:**
```bash
# Test with netcat
nc -zv localhost 8080

# Test with curl (for HTTP transport)
curl http://localhost:8080/health
```

**Verify transport configuration:**
```python
# For stdio transport
mcp = FastMCP("server", transport="stdio")

# For HTTP transport
mcp = FastMCP("server", transport="http", host="0.0.0.0", port=8080)
```

### 3. Tool Execution Errors

**Debug with detailed tracing:**
```python
@mcp.tool()
async def debug_tool(param: str) -> Dict[str, Any]:
    import traceback
    try:
        # Tool logic here
        result = await process(param)
        return {"result": result}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}
```

### 4. Performance Issues

**Profile async operations:**
```python
import asyncio
import time

async def measure_performance():
    tasks = []
    start = time.time()
    
    for i in range(100):
        tasks.append(mcp.tools["my_tool"](f"param_{i}"))
    
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    print(f"Processed {len(results)} requests in {duration:.2f}s")
    print(f"Average: {duration/len(results):.3f}s per request")
```

### 5. Memory Leaks

**Monitor memory usage:**
```python
import psutil
import os

@mcp.tool()
async def memory_check() -> Dict[str, Any]:
    process = psutil.Process(os.getpid())
    return {
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent()
    }
```

## Diagnostic Tools

### 1. Protocol Logger
```python
class ProtocolLogger:
    def __init__(self, mcp_server):
        self.server = mcp_server
        self.messages = []
    
    async def log_message(self, direction: str, message: Dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "message": message
        }
        self.messages.append(entry)
        
        if len(self.messages) > 1000:
            # Write to file and clear
            with open("protocol.log", "a") as f:
                for msg in self.messages:
                    f.write(json.dumps(msg) + "\n")
            self.messages.clear()
```

### 2. Health Check Endpoint
```python
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    checks = {
        "server": "ok",
        "database": "unknown",
        "cache": "unknown"
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except:
        checks["database"] = "error"
    
    # Check cache
    try:
        await cache.ping()
        checks["cache"] = "ok"
    except:
        checks["cache"] = "error"
    
    return {
        "status": "healthy" if all(v == "ok" for v in checks.values()) else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

## Getting Help

1. **Check logs first** - Most issues are visible in debug logs
2. **Minimal reproduction** - Create smallest example that shows the issue
3. **Protocol trace** - Include request/response messages
4. **Environment details** - Python version, FastMCP version, OS

### Community Resources
- MCP Discord Server
- GitHub Issues
- Stack Overflow tag: `mcp-protocol`
