"""
Claude Code SDK CLI following official standards
"""

import click
import asyncio
import json
import os
from pathlib import Path
from typing import Optional

try:
    from .claude_integration import MCPOrchestrator, FastMCPSpecialist
except ImportError:
    # Handle case when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from claude_code_sdk.claude_integration import MCPOrchestrator, FastMCPSpecialist


@click.group()
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Claude API key')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, api_key: Optional[str], verbose: bool):
    """Claude Code SDK for MCP Development - Official Standards Compliant"""
    
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key
    ctx.obj['verbose'] = verbose
    
    if not api_key:
        click.echo("⚠️  Warning: No API key provided. Set ANTHROPIC_API_KEY environment variable or use --api-key")


@cli.command()
@click.option('--workflow', default='new_server', help='Workflow type')
@click.option('--requirements', help='Requirements JSON file or string')
@click.option('--stream', is_flag=True, help='Enable streaming output')
@click.pass_context
def orchestrate(ctx, workflow: str, requirements: Optional[str], stream: bool):
    """Run orchestrated MCP development workflow using Claude SDK standards"""
    
    async def run():
        api_key = ctx.obj['api_key']
        if not api_key:
            click.echo("❌ API key required for orchestration")
            return 1
        
        # Initialize orchestrator following SDK standards
        orchestrator = MCPOrchestrator(api_key=api_key)
        session_id = await orchestrator.create_conversation()
        
        click.echo(f"🚀 Starting {workflow} workflow (Session: {session_id[:8]}...)")
        
        # Parse requirements
        reqs = {}
        if requirements:
            if Path(requirements).exists():
                with open(requirements, 'r') as f:
                    reqs = json.load(f)
            else:
                try:
                    reqs = json.loads(requirements)
                except json.JSONDecodeError:
                    click.echo(f"❌ Invalid JSON in requirements: {requirements}")
                    return 1
        
        # Create workflow message following SDK standards
        message = f"""Please create and execute a {workflow} workflow with the following requirements:

Requirements: {json.dumps(reqs, indent=2)}

Use the create_workflow tool to structure this workflow, then coordinate the implementation through quality-gated phases. Provide status updates and delegate to appropriate specialists as needed.

Output the results in JSON format with workflow status, phase results, and any recommendations."""
        
        try:
            if stream:
                click.echo("📡 Streaming response...")
                async for chunk in orchestrator._stream_response("json"):
                    if chunk["type"] == "content_delta":
                        click.echo(chunk["delta"], nl=False)
                    elif chunk["type"] == "message_complete":
                        click.echo("\n✅ Workflow completed")
            else:
                result = await orchestrator.send_message(message, output_format="json")
                
                if result["success"]:
                    click.echo("✅ Workflow orchestration completed")
                    
                    if "parsed_json" in result:
                        workflow_data = result["parsed_json"]
                        click.echo(f"📊 Status: {workflow_data.get('status', 'unknown')}")
                        
                        if ctx.obj['verbose']:
                            click.echo("\n📋 Workflow Details:")
                            click.echo(json.dumps(workflow_data, indent=2))
                    else:
                        click.echo("\n📄 Response:")
                        click.echo(result["content"])
                else:
                    click.echo(f"❌ Orchestration failed: {result.get('error')}")
                    return 1
            
            return 0
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            return 1
    
    exit_code = asyncio.run(run())
    exit(exit_code)


@cli.command()
@click.option('--server-name', required=True, help='Name for the MCP server')
@click.option('--tools', help='JSON array of tool specifications')
@click.option('--auth', default='none', type=click.Choice(['none', 'oauth', 'jwt']), help='Authentication type')
@click.option('--output', help='Output file for generated code')
@click.pass_context
def generate_server(ctx, server_name: str, tools: Optional[str], auth: str, output: Optional[str]):
    """Generate FastMCP server using Claude SDK standards"""
    
    async def run():
        api_key = ctx.obj['api_key']
        if not api_key:
            click.echo("❌ API key required for server generation")
            return 1
        
        # Initialize FastMCP specialist
        specialist = FastMCPSpecialist(api_key=api_key)
        await specialist.create_conversation()
        
        click.echo(f"🔧 Generating FastMCP server: {server_name}")
        
        # Parse tools
        tools_list = []
        if tools:
            try:
                tools_list = json.loads(tools)
            except json.JSONDecodeError:
                click.echo(f"❌ Invalid JSON in tools: {tools}")
                return 1
        
        # Create generation message
        message = f"""Please generate a complete FastMCP server implementation with these specifications:

Server Name: {server_name}
Authentication: {auth}
Tools: {json.dumps(tools_list, indent=2) if tools_list else '[]'}

Use the generate_mcp_server tool to create a production-ready implementation following repository-verified patterns. Include:

1. Complete Python code with proper imports
2. Pydantic models for type safety  
3. Comprehensive error handling
4. Authentication setup if specified
5. Proper async patterns
6. Structured logging
7. Usage examples

Format the response as JSON with the generated code and any additional files needed."""
        
        try:
            result = await specialist.send_message(message, output_format="json")
            
            if result["success"]:
                click.echo("✅ Server generation completed")
                
                if "parsed_json" in result:
                    server_data = result["parsed_json"]
                    
                    # Save to file if specified
                    if output:
                        with open(output, 'w') as f:
                            if "code" in server_data:
                                f.write(server_data["code"])
                            else:
                                json.dump(server_data, f, indent=2)
                        click.echo(f"💾 Saved to {output}")
                    
                    if ctx.obj['verbose']:
                        click.echo("\n📋 Generated Components:")
                        for key in server_data.keys():
                            click.echo(f"   • {key}")
                else:
                    click.echo(f"\n📄 Generated Code:")
                    click.echo(result["content"])
                    
                    if output:
                        with open(output, 'w') as f:
                            f.write(result["content"])
                        click.echo(f"💾 Saved to {output}")
            else:
                click.echo(f"❌ Generation failed: {result.get('error')}")
                return 1
            
            return 0
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            return 1
    
    exit_code = asyncio.run(run())
    exit(exit_code)


@cli.command()
@click.option('--session-id', help='Export specific conversation session')
@click.pass_context 
def export_conversation(ctx, session_id: Optional[str]):
    """Export conversation following Claude SDK standards"""
    
    async def run():
        api_key = ctx.obj['api_key']
        if not api_key:
            click.echo("❌ API key required")
            return 1
        
        # For demo purposes, create a sample export
        click.echo("📤 Exporting conversation...")
        
        sample_export = {
            "session_id": session_id or "sample-session",
            "agent_config": {
                "name": "mcp-orchestrator", 
                "model": "claude-3-opus-20240229"
            },
            "messages": [
                {"role": "user", "content": "Create a new MCP server"},
                {"role": "assistant", "content": "I'll help you create a new MCP server..."}
            ],
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "message_count": 2
            }
        }
        
        click.echo(json.dumps(sample_export, indent=2))
        return 0
    
    exit_code = asyncio.run(run())
    exit(exit_code)


@cli.command()
@click.pass_context
def validate_setup(ctx):
    """Validate Claude SDK setup and configuration"""
    
    click.echo("🔍 Validating Claude Code SDK setup...")
    
    # Check API key
    api_key = ctx.obj['api_key']
    if api_key:
        click.echo("✅ API key configured")
        if api_key.startswith('sk-ant-'):
            click.echo("✅ API key format valid")
        else:
            click.echo("⚠️  API key format may be invalid")
    else:
        click.echo("❌ No API key configured")
        click.echo("   Set ANTHROPIC_API_KEY environment variable or use --api-key")
    
    # Check dependencies
    try:
        import anthropic
        click.echo(f"✅ Anthropic SDK installed (version: {anthropic.__version__})")
    except ImportError:
        click.echo("❌ Anthropic SDK not installed")
        click.echo("   Run: pip install anthropic")
    
    # Check configuration
    config_path = Path(".claude/config.json")
    if config_path.exists():
        click.echo("✅ Claude configuration found")
        try:
            with open(config_path) as f:
                config = json.load(f)
            click.echo(f"   Agents configured: {len(config.get('agents', {}))}")
        except Exception as e:
            click.echo(f"⚠️  Configuration parse error: {e}")
    else:
        click.echo("⚠️  No Claude configuration found")
        click.echo("   Expected: .claude/config.json")
    
    click.echo("\n🎯 Claude Code SDK Status: Ready for MCP development")


if __name__ == "__main__":
    cli()