#!/usr/bin/env python3
"""
Minimal FastMCP Server Example

A basic MCP server demonstrating core FastMCP patterns with proper error handling,
type safety, and repository-verified implementation patterns.

Usage:
    python server.py

This server provides:
- Basic tool implementation with structured outputs
- Resource access patterns
- Prompt templates
- Input validation and error handling
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import json
import time
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("minimal-mcp-server")

# Structured response models
class AnalysisResult(BaseModel):
    """Structured analysis result with validation"""
    status: str = Field(description="Operation status: success, error, or warning")
    data: Dict[str, Any] = Field(description="Analysis results and findings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: float = Field(default_factory=time.time, description="Result timestamp")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['success', 'error', 'warning']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

class DataSummary(BaseModel):
    """Data summary with statistics"""
    total_items: int = Field(ge=0, description="Total number of items")
    categories: List[str] = Field(description="Data categories found")
    summary: str = Field(description="Human-readable summary")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

# Tools implementation
@mcp.tool
def analyze_text(
    text: str,
    analysis_type: str = "basic"
) -> AnalysisResult:
    """
    Analyze text content with structured output.
    
    This tool demonstrates basic text analysis with proper input validation,
    error handling, and structured response format.
    
    Args:
        text: Text content to analyze (required, max 10000 characters)
        analysis_type: Type of analysis - 'basic', 'detailed', or 'sentiment'
    
    Returns:
        AnalysisResult with status, data, and metadata
    """
    try:
        # Input validation
        if not text or not text.strip():
            return AnalysisResult(
                status="error",
                data={"error": "Text input cannot be empty"},
                metadata={"analysis_type": analysis_type}
            )
        
        if len(text) > 10000:
            return AnalysisResult(
                status="error",
                data={"error": "Text too long (max 10000 characters)"},
                metadata={"text_length": len(text), "analysis_type": analysis_type}
            )
        
        # Basic text analysis
        words = text.split()
        sentences = text.split('.')
        
        analysis_data = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "text_length": len(text)
        }
        
        # Enhanced analysis based on type
        if analysis_type == "detailed":
            unique_words = set(word.lower().strip('.,!?;:"()[]') for word in words)
            analysis_data.update({
                "unique_words": len(unique_words),
                "vocabulary_richness": len(unique_words) / len(words) if words else 0,
                "most_common_words": [word for word in words[:5]]  # Simple implementation
            })
        
        elif analysis_type == "sentiment":
            # Simple sentiment analysis (placeholder)
            positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
            negative_words = ["bad", "terrible", "awful", "horrible", "poor"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            analysis_data.update({
                "sentiment": sentiment,
                "positive_indicators": positive_count,
                "negative_indicators": negative_count
            })
        
        return AnalysisResult(
            status="success",
            data=analysis_data,
            metadata={
                "analysis_type": analysis_type,
                "processing_time": 0.001  # Simulated processing time
            }
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return AnalysisResult(
            status="error",
            data={"error": f"Analysis failed: {str(e)}"},
            metadata={"analysis_type": analysis_type}
        )

@mcp.tool
def calculate_statistics(
    numbers: List[float]
) -> Dict[str, Any]:
    """
    Calculate basic statistics for a list of numbers.
    
    Demonstrates list input handling, mathematical operations,
    and comprehensive error handling.
    
    Args:
        numbers: List of numbers to analyze
    
    Returns:
        Dictionary with statistical calculations
    """
    try:
        if not numbers:
            return {"error": "Numbers list cannot be empty"}
        
        if len(numbers) > 1000:
            return {"error": "Too many numbers (max 1000)"}
        
        # Validate all inputs are numbers
        try:
            valid_numbers = [float(n) for n in numbers]
        except (ValueError, TypeError):
            return {"error": "All inputs must be valid numbers"}
        
        # Calculate statistics
        n = len(valid_numbers)
        total = sum(valid_numbers)
        mean = total / n
        
        # Calculate median
        sorted_numbers = sorted(valid_numbers)
        if n % 2 == 0:
            median = (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
        else:
            median = sorted_numbers[n//2]
        
        # Calculate variance and standard deviation
        variance = sum((x - mean) ** 2 for x in valid_numbers) / n
        std_dev = variance ** 0.5
        
        return {
            "success": True,
            "count": n,
            "sum": total,
            "mean": round(mean, 4),
            "median": round(median, 4),
            "min": min(valid_numbers),
            "max": max(valid_numbers),
            "range": max(valid_numbers) - min(valid_numbers),
            "variance": round(variance, 4),
            "standard_deviation": round(std_dev, 4)
        }
        
    except Exception as e:
        logger.error(f"Statistics calculation error: {str(e)}")
        return {"error": f"Calculation failed: {str(e)}"}

@mcp.tool
def generate_summary(
    items: List[str],
    category: str = "general"
) -> DataSummary:
    """
    Generate a summary of data items.
    
    Demonstrates complex data processing with Pydantic model validation
    and business logic implementation.
    
    Args:
        items: List of items to summarize
        category: Category for context-aware summarization
    
    Returns:
        DataSummary with structured analysis
    """
    try:
        if not items:
            return DataSummary(
                total_items=0,
                categories=["empty"],
                summary="No items provided for analysis",
                confidence=1.0
            )
        
        # Analyze items
        total_items = len(items)
        
        # Simple categorization based on content patterns
        categories = set()
        for item in items:
            item_lower = item.lower()
            if any(word in item_lower for word in ["email", "@", "mail"]):
                categories.add("email")
            elif any(word in item_lower for word in ["phone", "tel", "call"]):
                categories.add("phone")
            elif any(word in item_lower for word in ["http", "www", "url"]):
                categories.add("url")
            elif any(word in item_lower for word in ["date", "time", "day"]):
                categories.add("temporal")
            else:
                categories.add("text")
        
        # Generate context-aware summary
        category_list = list(categories)
        
        if category == "technical":
            summary = f"Technical analysis of {total_items} items across {len(category_list)} categories"
        elif category == "business":
            summary = f"Business summary: {total_items} items with focus on {', '.join(category_list)}"
        else:
            summary = f"General summary: {total_items} items categorized as {', '.join(category_list)}"
        
        # Calculate confidence based on data quality
        confidence = min(1.0, max(0.5, (total_items / 100)))  # Higher confidence with more data
        
        return DataSummary(
            total_items=total_items,
            categories=category_list,
            summary=summary,
            confidence=round(confidence, 2)
        )
        
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        # Return error as valid DataSummary
        return DataSummary(
            total_items=0,
            categories=["error"],
            summary=f"Summary generation failed: {str(e)}",
            confidence=0.0
        )

# Resource implementation
@mcp.resource("file://config/{config_name}")
def get_config(config_name: str) -> str:
    """
    Retrieve configuration data.
    
    Demonstrates resource pattern with URI templating and proper validation.
    
    Args:
        config_name: Name of the configuration to retrieve
    
    Returns:
        JSON string with configuration data
    """
    try:
        # Validate config name
        if not config_name or not config_name.strip():
            raise ValueError("Config name cannot be empty")
        
        # Simple config simulation
        configs = {
            "server": {
                "host": "localhost",
                "port": 8000,
                "debug": False
            },
            "database": {
                "url": "postgresql://localhost:5432/mcp_db",
                "pool_size": 10,
                "timeout": 30
            },
            "cache": {
                "type": "redis",
                "url": "redis://localhost:6379",
                "ttl": 3600
            }
        }
        
        if config_name not in configs:
            available_configs = list(configs.keys())
            raise ValueError(f"Config '{config_name}' not found. Available: {available_configs}")
        
        return json.dumps(configs[config_name], indent=2)
        
    except Exception as e:
        logger.error(f"Config retrieval error: {str(e)}")
        return json.dumps({"error": str(e)})

# Prompt template
@mcp.prompt
def analysis_prompt(
    data_type: str,
    detail_level: str = "medium"
) -> str:
    """
    Generate analysis prompt template.
    
    Demonstrates prompt pattern with dynamic content generation
    and parameter-based customization.
    
    Args:
        data_type: Type of data to analyze
        detail_level: Level of detail - 'basic', 'medium', or 'detailed'
    
    Returns:
        Formatted prompt string
    """
    detail_instructions = {
        "basic": "Provide a high-level overview with key findings",
        "medium": "Include detailed analysis with supporting evidence",
        "detailed": "Comprehensive analysis with methodology, findings, and recommendations"
    }
    
    instruction = detail_instructions.get(detail_level, detail_instructions["medium"])
    
    return f"""
Please analyze the following {data_type} data:

Analysis Requirements:
- {instruction}
- Focus on actionable insights
- Include confidence levels for conclusions
- Highlight any anomalies or notable patterns

Expected Output Format:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Recommendations
5. Confidence Assessment

Please ensure your analysis is thorough, objective, and provides clear value to the reader.
"""

# Server lifecycle management
async def initialize_server():
    """Initialize server resources"""
    logger.info("Initializing Minimal MCP Server...")
    logger.info("Server ready for connections")

async def cleanup_server():
    """Cleanup server resources"""
    logger.info("Shutting down Minimal MCP Server...")

if __name__ == "__main__":
    try:
        # Initialize server
        asyncio.run(initialize_server())
        
        # Run the server
        logger.info("Starting Minimal MCP Server...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        asyncio.run(cleanup_server())