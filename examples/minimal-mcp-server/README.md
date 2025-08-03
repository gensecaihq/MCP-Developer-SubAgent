# Minimal MCP Server Example

A basic FastMCP server demonstrating core patterns and best practices for MCP development.

## Features

- **Tool Implementation**: Text analysis, statistics calculation, data summarization
- **Resource Access**: Configuration retrieval with URI templating
- **Prompt Templates**: Dynamic prompt generation with parameterization
- **Type Safety**: Comprehensive Pydantic model validation
- **Error Handling**: Robust error boundaries with graceful degradation
- **Logging**: Structured logging for debugging and monitoring

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   python server.py
   ```

3. **Test with Claude Desktop**:
   Add to your MCP client configuration:
   ```json
   {
     "mcp": {
       "servers": {
         "minimal-server": {
           "command": "python",
           "args": ["/path/to/server.py"],
           "transport": "stdio"
         }
       }
     }
   }
   ```

## Available Tools

### `analyze_text`
Analyze text content with multiple analysis types:
- **basic**: Word count, sentence count, basic statistics
- **detailed**: Vocabulary analysis, word frequency
- **sentiment**: Simple sentiment analysis

**Example**:
```python
result = analyze_text("Hello world! This is a test.", "detailed")
```

### `calculate_statistics`
Calculate statistics for numerical data:
- Mean, median, mode
- Standard deviation, variance
- Min, max, range

**Example**:
```python
stats = calculate_statistics([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
```

### `generate_summary`
Generate intelligent summaries of data items:
- Automatic categorization
- Context-aware summarization
- Confidence scoring

**Example**:
```python
summary = generate_summary(["item1", "item2", "item3"], "technical")
```

## Available Resources

### `file://config/{config_name}`
Retrieve configuration data for different components:
- `server`: Server configuration
- `database`: Database settings
- `cache`: Cache configuration

**Example**:
```python
config = get_config("server")
```

## Available Prompts

### `analysis_prompt`
Generate analysis prompt templates with customizable detail levels:
- **basic**: High-level overview
- **medium**: Detailed analysis with evidence
- **detailed**: Comprehensive analysis with methodology

**Example**:
```python
prompt = analysis_prompt("customer_data", "detailed")
```

## Error Handling

The server implements comprehensive error handling:
- Input validation with clear error messages
- Graceful degradation for partial failures
- Structured error responses with debugging information
- Logging for troubleshooting and monitoring

## Type Safety

All tools use Pydantic models for:
- Input validation
- Output structure definition
- Automatic schema generation
- Runtime type checking

## Architecture Patterns

This example demonstrates:
- **Repository-Verified Patterns**: Based on official FastMCP examples
- **Production-Ready Code**: Error handling, logging, validation
- **Academic Standards**: Comprehensive documentation and type safety
- **Enterprise Considerations**: Structured responses, monitoring hooks

## Next Steps

Use this minimal server as a foundation for:
1. Adding domain-specific tools and resources
2. Implementing authentication and authorization
3. Adding database connectivity and caching
4. Integrating monitoring and observability
5. Scaling to production environments

For more advanced examples, see:
- `../enterprise-auth-server/` - OAuth 2.1 authentication
- `../performance-optimized/` - High-performance patterns
- `../multi-transport-server/` - Multiple transport support