"""
Database MCP Server Example
Shows how to create database tools with proper connection management
"""

from fastmcp import FastMCP, Tool
import asyncpg
from typing import List, Dict, Any, Optional
import asyncio

mcp = FastMCP("database-server", version="1.0.0")

# Global connection pool
pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            "postgresql://user:password@localhost/dbname",
            min_size=1,
            max_size=10
        )
    return pool

@mcp.tool()
async def query_database(
    query: str,
    params: Optional[List[Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a database query
    
    Args:
        query: SQL query to execute
        params: Optional query parameters
        
    Returns:
        List of dictionaries representing rows
    """
    pool = await get_pool()
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *(params or []))
            return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
async def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Get schema information for a table
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with table schema information
    """
    pool = await get_pool()
    
    query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = $1
    ORDER BY ordinal_position
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, table_name)
            columns = [dict(row) for row in rows]
            return {
                "table_name": table_name,
                "columns": columns
            }
    except Exception as e:
        return {"error": str(e)}

# Cleanup on shutdown
@mcp.startup()
async def startup():
    """Initialize resources on startup"""
    await get_pool()

@mcp.shutdown()
async def shutdown():
    """Clean up resources on shutdown"""
    global pool
    if pool:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(mcp.run())
