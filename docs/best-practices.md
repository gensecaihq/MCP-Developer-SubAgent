# MCP Development Best Practices

## 1. Tool Design

### Input Validation
Always validate tool inputs:
```python
@mcp.tool()
async def safe_tool(value: int) -> Dict[str, Any]:
    if value < 0:
        raise ValueError("Value must be non-negative")
    return {"result": value * 2}
```

### Clear Documentation
```python
@mcp.tool()
async def well_documented_tool(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for items matching the query.
    
    Args:
        query: Search query string (min 3 characters)
        limit: Maximum results to return (1-100)
        
    Returns:
        List of matching items with id and name
        
    Raises:
        ValueError: If query is too short or limit out of range
    """
    # Implementation
```

## 2. Error Handling

### Graceful Degradation
```python
@mcp.tool()
async def robust_tool(param: str) -> Dict[str, Any]:
    try:
        result = await process_data(param)
        return {"success": True, "data": result}
    except ValidationError as e:
        return {"success": False, "error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Internal error", "code": "INTERNAL_ERROR"}
```

## 3. Performance

### Connection Pooling
```python
class ConnectionManager:
    def __init__(self):
        self._pool = None
    
    async def get_connection(self):
        if not self._pool:
            self._pool = await create_pool()
        return self._pool.acquire()

conn_manager = ConnectionManager()

@mcp.tool()
async def efficient_tool():
    async with await conn_manager.get_connection() as conn:
        return await conn.fetch("SELECT ...")
```

### Caching
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def expensive_computation(param: str) -> str:
    # Expensive operation
    return hashlib.sha256(param.encode()).hexdigest()

@mcp.tool()
async def cached_tool(param: str) -> str:
    return expensive_computation(param)
```

## 4. Testing

### Unit Testing Tools
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_my_tool():
    # Mock dependencies
    mock_db = AsyncMock()
    mock_db.fetch.return_value = [{"id": 1, "name": "Test"}]
    
    # Test the tool
    result = await my_tool("test_query")
    assert result["success"] is True
    assert len(result["data"]) == 1
```

### Integration Testing
```python
@pytest.mark.asyncio
async def test_mcp_server():
    # Start server in test mode
    server = FastMCP("test-server")
    
    # Simulate client interaction
    response = await server.handle_tool_call({
        "name": "my_tool",
        "arguments": {"param": "test"}
    })
    
    assert response["success"] is True
```

## 5. Security

### Input Sanitization
```python
import re

@mcp.tool()
async def secure_query_tool(query: str) -> List[Dict[str, Any]]:
    # Sanitize input
    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query)
    
    # Use parameterized queries
    return await db.fetch(
        "SELECT * FROM items WHERE name LIKE $1",
        f"%{safe_query}%"
    )
```

### Rate Limiting
```python
from collections import defaultdict
import time

rate_limits = defaultdict(lambda: {"count": 0, "reset": time.time()})

@mcp.tool()
async def rate_limited_tool(user_id: str) -> Dict[str, Any]:
    # Check rate limit
    now = time.time()
    user_limit = rate_limits[user_id]
    
    if now > user_limit["reset"]:
        user_limit["count"] = 0
        user_limit["reset"] = now + 60  # Reset every minute
    
    if user_limit["count"] >= 10:
        return {"error": "Rate limit exceeded"}
    
    user_limit["count"] += 1
    
    # Proceed with tool logic
    return {"result": "Success"}
```
