"""
Setup configuration for Claude MCP SDK
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
README_PATH = Path(__file__).parent / "README.md"
long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

# Read requirements
REQUIREMENTS_PATH = Path(__file__).parent / "requirements.txt"
if REQUIREMENTS_PATH.exists():
    with open(REQUIREMENTS_PATH, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0", 
        "aiofiles>=0.8.0",
        "black>=22.0.0",
        "click>=8.0.0",
        "structlog>=22.0.0"
    ]

setup(
    name="claude-mcp-sdk",
    version="1.0.0",
    author="GenSecAI.org",
    author_email="opensource@gensecai.org",
    description="Claude Code SDK for programmatic MCP development with multi-agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gensecaihq/MCP-Developer-SubAgent",
    packages=find_packages(exclude=["tests*", "examples*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "coverage>=7.0.0"
        ],
        "auth": [
            "pyjwt>=2.0.0",
            "cryptography>=3.4.0"
        ],
        "mcp": [
            "fastmcp>=0.1.0"
        ],
        "full": [
            "pyjwt>=2.0.0",
            "cryptography>=3.4.0",
            "structlog>=22.0.0",
            "black>=22.0.0"
        ],
        "monitoring": [
            "opentelemetry-api>=1.15.0",
            "opentelemetry-sdk>=1.15.0",
            "prometheus-client>=0.16.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "claude-mcp=claude_code_sdk.cli:cli",
            "mcp-orchestrate=claude_code_sdk.cli:orchestrate", 
        ],
        "claude_code_sdk.agents": [
            "orchestrator=claude_code_sdk.claude_integration:MCPOrchestrator",
            "fastmcp-specialist=claude_code_sdk.claude_integration:FastMCPSpecialist"
        ]
    },
    include_package_data=True,
    package_data={
        "claude": ["*.json", "*.md"],
        "claude.sdk": ["*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/gensecaihq/MCP-Developer-SubAgent/issues",
        "Source": "https://github.com/gensecaihq/MCP-Developer-SubAgent",
        "Documentation": "https://docs.claude-mcp-sdk.dev",
    },
    keywords=[
        "mcp", "model-context-protocol", "claude", "fastmcp", "agents", 
        "orchestration", "development", "automation", "ai"
    ]
)