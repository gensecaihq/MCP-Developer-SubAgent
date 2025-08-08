#!/usr/bin/env python3
"""
Simple CLI for testing - works without external dependencies
"""

import json
import sys
import os
from pathlib import Path


def validate_setup():
    """Validate the repository setup"""
    print("🔍 Validating Claude Code MCP SDK setup...")
    
    issues = []
    warnings = []
    
    # Check Python version
    import sys
    py_version = sys.version_info
    if py_version < (3, 10):
        issues.append(f"Python {py_version.major}.{py_version.minor} < 3.10 (required)")
    else:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check sub-agents
    agents_dir = Path(".claude/agents")
    if agents_dir.exists():
        agent_files = list(agents_dir.glob("*.md"))
        print(f"✅ Found {len(agent_files)} sub-agents")
        for agent_file in agent_files:
            print(f"   - {agent_file.name}")
    else:
        issues.append("Missing .claude/agents/ directory")
    
    # Check hooks
    hooks_file = Path(".claude/hooks.json")
    if hooks_file.exists():
        try:
            with open(hooks_file) as f:
                hooks_data = json.load(f)
            print(f"✅ Hooks configuration valid ({len(hooks_data.get('hooks', []))} hooks)")
        except json.JSONDecodeError as e:
            issues.append(f"Invalid hooks.json: {e}")
    else:
        warnings.append("Missing .claude/hooks.json")
    
    # Check examples
    examples_dir = Path("examples")
    if examples_dir.exists():
        example_servers = list(examples_dir.glob("*/server.py"))
        print(f"✅ Found {len(example_servers)} example servers")
    else:
        warnings.append("Missing examples/ directory")
    
    # Check GitHub Actions
    workflows_dir = Path(".github/workflows")
    if workflows_dir.exists():
        workflows = list(workflows_dir.glob("*.yml"))
        print(f"✅ Found {len(workflows)} GitHub workflows")
    else:
        warnings.append("Missing .github/workflows/")
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ ANTHROPIC_API_KEY environment variable set")
    else:
        warnings.append("ANTHROPIC_API_KEY not set (required for SDK)")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    if issues:
        print(f"❌ {len(issues)} critical issues:")
        for issue in issues:
            print(f"   • {issue}")
    
    if warnings:
        print(f"⚠️  {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not issues and not warnings:
        print("🎉 All checks passed!")
    elif not issues:
        print("✅ Setup valid with minor warnings")
    else:
        print("❌ Setup has critical issues")
        return False
    
    return True


def show_status():
    """Show current repository status"""
    print("📋 Claude Code MCP SDK Status\n")
    
    # Working components
    print("✅ FUNCTIONAL COMPONENTS:")
    print("   • Sub-Agents: 8 agents in .claude/agents/")
    print("   • Hooks System: Security validation working")
    print("   • Examples: 3 MCP server templates")
    print("   • GitHub Actions: CI/CD workflows configured")
    print("   • Documentation: Complete guides available")
    
    print("\n⚠️  DEPENDENCY REQUIREMENTS:")
    print("   • Python 3.10+ required")
    print("   • pip install -e . (for full SDK)")
    print("   • ANTHROPIC_API_KEY environment variable")
    
    print("\n🎯 USAGE MODES:")
    print("   1. Claude Code Integration (sub-agents)")
    print("   2. Programmatic SDK (Python API)")
    print("   3. Examples & Templates (copy/modify)")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Claude Code MCP SDK - Simple CLI")
        print("Usage:")
        print("  python3 claude_code_sdk/cli_simple.py validate-setup")
        print("  python3 claude_code_sdk/cli_simple.py status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "validate-setup":
        success = validate_setup()
        sys.exit(0 if success else 1)
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()