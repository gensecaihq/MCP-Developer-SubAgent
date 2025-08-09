# Cross-Platform Installation Guide

## 🚀 Quick Start (All Platforms)

### 1. Check Compatibility
```bash
# Check Python version (minimum 3.8, recommended 3.10+)
python --version    # Windows/some Linux
python3 --version   # macOS/Linux
```

### 2. Basic Installation

#### Windows (Command Prompt/PowerShell)
```batch
# Clone repository
git clone https://github.com/yourusername/MCP-Developer-SubAgent.git
cd MCP-Developer-SubAgent

# Install basic dependencies (no build tools needed)
python -m pip install -e .

# Set environment variable
set ANTHROPIC_API_KEY=sk-ant-your-key-here
# Or for PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Validate setup
python claude_code_sdk\cli_simple.py validate-setup
```

#### macOS/Linux
```bash
# Clone repository  
git clone https://github.com/yourusername/MCP-Developer-SubAgent.git
cd MCP-Developer-SubAgent

# Install basic dependencies
pip install -e .

# Set environment variable
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Validate setup
python3 claude_code_sdk/cli_simple.py validate-setup
```

## 🔧 Installation Options

### Basic Installation (Recommended)
- **Windows**: `python -m pip install -e .`
- **macOS/Linux**: `pip install -e .`

Includes: Core functionality, sub-agents, examples, CLI tools

### With Authentication Support
- **Windows**: `python -m pip install -e .[auth]`
- **macOS/Linux**: `pip install -e .[auth]`

Adds: JWT authentication, cryptography (requires build tools)

### Full Installation
- **Windows**: `python -m pip install -e .[full]`
- **macOS/Linux**: `pip install -e .[full]`

Adds: All features, development tools, formatting

## 🛠️ Platform-Specific Requirements

### Windows
**Python**: Install from [python.org](https://python.org) or Microsoft Store

**For Authentication Features** (optional):
- Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Or use pre-built wheels (usually automatic)

### macOS
**Python**: Use system Python 3.8+ or install via Homebrew:
```bash
brew install python@3.10
```

**For Authentication Features** (optional):
```bash
xcode-select --install  # Install command line tools
```

### Linux (Ubuntu/Debian)
**Python**: Usually pre-installed, or:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**For Authentication Features** (optional):
```bash
sudo apt install build-essential python3-dev libssl-dev
```

### Linux (RHEL/CentOS/Fedora)
**Python**: Usually pre-installed, or:
```bash
sudo yum install python3 python3-pip  # RHEL/CentOS
sudo dnf install python3 python3-pip  # Fedora
```

**For Authentication Features** (optional):
```bash
sudo yum install gcc python3-devel openssl-devel  # RHEL/CentOS
sudo dnf install gcc python3-devel openssl-devel  # Fedora
```

## ⚡ What Works Without Installation

Even without `pip install`, you can use:

### 1. Repository Validation
```bash
# Windows
python claude_code_sdk\cli_simple.py validate-setup

# macOS/Linux  
python3 claude_code_sdk/cli_simple.py validate-setup
```

### 2. Copy Example Code
```bash
# Windows
copy examples\minimal-mcp-server\server.py my_server.py

# macOS/Linux
cp examples/minimal-mcp-server/server.py my_server.py
```

### 3. Security Hooks (with Python available)
```bash
# Test hook validation
echo '{"toolType": "Write", "filePath": "test.py"}' | python claude_code_sdk/cli_simple.py
```

## 🚨 Troubleshooting

### "FastMCP not found" Error
FastMCP is optional and may not be available on PyPI. Use:
```bash
# Install without FastMCP
pip install -e .

# Or try with MCP extras (if available)
pip install -e .[mcp]
```

### Python Version Too Old
**Ubuntu 20.04** (Python 3.8):
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-pip
python3.10 -m pip install -e .
```

**macOS older versions**:
```bash
brew install python@3.10
python3.10 -m pip install -e .
```

### Build Failures (cryptography)
Try basic installation without auth features:
```bash
pip install -e .  # Skip [auth] extras
```

Or use conda which has pre-built packages:
```bash
conda install cryptography
pip install -e .
```

### Permission Errors
**Windows**: Run Command Prompt as Administrator  
**macOS/Linux**: Use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -e .
```

## ✅ Verification

After installation, verify everything works:

### Windows
```batch
python claude_code_sdk\cli_simple.py validate-setup
python claude_code_sdk\cli_simple.py status
```

### macOS/Linux
```bash
python3 claude_code_sdk/cli_simple.py validate-setup
python3 claude_code_sdk/cli_simple.py status
```

### Expected Output
```
🔍 Validating Claude Code MCP SDK setup...
✅ Python 3.x.x
✅ Found 8 sub-agents
✅ Hooks configuration valid (5 hooks)
✅ Found 2 example servers
✅ Found 1 GitHub workflows
📊 Validation Summary: Setup valid
```

## 🎯 Next Steps

1. **Check Status**: Run the status command to see platform-specific installation notes
2. **Try Examples**: Copy and modify example servers
3. **Set API Key**: Add your Anthropic API key for full SDK features
4. **Use Sub-Agents**: If you have Claude Code, sub-agents will auto-activate

## 💡 Tips

- **Start Basic**: Use basic installation first, add extras as needed
- **Use Virtual Environments**: Prevents conflicts with system packages
- **Check Platform Notes**: Run status command for platform-specific advice
- **Skip Optional Deps**: Authentication features are optional for most use cases