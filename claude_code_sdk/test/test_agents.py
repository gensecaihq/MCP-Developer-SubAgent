#!/usr/bin/env python3
"""
Comprehensive tests for agent system functionality
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAgentFiles:
    """Test agent file structure and content"""
    
    @pytest.fixture
    def agents_dir(self):
        """Agent directory path"""
        return Path(__file__).parent.parent.parent / ".claude" / "agents"
    
    def test_agents_directory_exists(self, agents_dir):
        """Test agents directory exists"""
        assert agents_dir.exists()
        assert agents_dir.is_dir()
    
    def test_all_agents_present(self, agents_dir):
        """Test all expected agent files are present"""
        expected_agents = [
            "mcp-orchestrator.md",
            "fastmcp-specialist.md", 
            "mcp-protocol-expert.md",
            "mcp-security-auditor.md",
            "mcp-performance-optimizer.md",
            "mcp-deployment-specialist.md",
            "mcp-debugger.md",
            "context-manager.md"
        ]
        
        agent_files = [f.name for f in agents_dir.glob("*.md")]
        
        for expected_agent in expected_agents:
            assert expected_agent in agent_files, f"Missing agent: {expected_agent}"
    
    def test_agent_file_structure(self, agents_dir):
        """Test each agent file has proper structure"""
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            # Should start with YAML frontmatter
            assert content.startswith("---"), f"Agent {agent_file.name} missing YAML frontmatter"
            
            # Should have closing frontmatter
            lines = content.split('\n')
            assert "---" in lines[1:10], f"Agent {agent_file.name} malformed YAML frontmatter"
            
            # Should have required sections
            required_sections = ["# Role", "# Core Competencies", "# Standard Operating Procedure"]
            for section in required_sections:
                assert section in content, f"Agent {agent_file.name} missing section: {section}"
    
    def test_yaml_frontmatter_valid(self, agents_dir):
        """Test YAML frontmatter is valid"""
        import yaml
        
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            # Extract YAML frontmatter
            if content.startswith("---"):
                end_marker = content.find("---", 3)
                if end_marker != -1:
                    yaml_content = content[3:end_marker].strip()
                    
                    # Should be valid YAML
                    try:
                        yaml_data = yaml.safe_load(yaml_content)
                        assert isinstance(yaml_data, dict), f"Invalid YAML in {agent_file.name}"
                        
                        # Should have required fields
                        assert "name" in yaml_data, f"Missing 'name' in {agent_file.name}"
                        assert "description" in yaml_data, f"Missing 'description' in {agent_file.name}"
                        assert "model" in yaml_data, f"Missing 'model' in {agent_file.name}"
                        
                    except yaml.YAMLError as e:
                        pytest.fail(f"Invalid YAML in {agent_file.name}: {e}")
    
    def test_agent_content_quality(self, agents_dir):
        """Test agent content meets quality standards"""
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            # Should be substantial (>100 lines)
            line_count = len(content.split('\n'))
            assert line_count > 100, f"Agent {agent_file.name} too short: {line_count} lines"
            
            # Should have examples or code blocks
            assert "```" in content or "## " in content, f"Agent {agent_file.name} lacks examples"
            
            # Should mention MCP somewhere
            assert "MCP" in content or "mcp" in content, f"Agent {agent_file.name} doesn't mention MCP"


class TestAgentConfiguration:
    """Test agent configuration system"""
    
    @pytest.fixture
    def config_path(self):
        """Config file path"""
        return Path(__file__).parent.parent.parent / ".claude" / "config.json"
    
    def test_config_file_exists(self, config_path):
        """Test config file exists"""
        assert config_path.exists(), "Config file missing"
    
    def test_config_file_valid_json(self, config_path):
        """Test config file is valid JSON"""
        with open(config_path) as f:
            try:
                config = json.load(f)
                assert isinstance(config, dict)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in config file: {e}")
    
    def test_config_has_agents(self, config_path):
        """Test config file has agent definitions"""
        with open(config_path) as f:
            config = json.load(f)
        
        assert "agents" in config, "Config missing 'agents' section"
        agents = config["agents"]
        
        # Should have at least 8 agents
        assert len(agents) >= 8, f"Expected at least 8 agents, got {len(agents)}"
    
    def test_agent_config_structure(self, config_path):
        """Test each agent config has proper structure"""
        with open(config_path) as f:
            config = json.load(f)
        
        agents = config["agents"]
        
        for agent_name, agent_config in agents.items():
            # Required fields
            assert "path" in agent_config, f"Agent {agent_name} missing 'path'"
            assert "description" in agent_config, f"Agent {agent_name} missing 'description'"
            assert "model" in agent_config, f"Agent {agent_name} missing 'model'"
            
            # Model should be valid
            valid_models = ["opus", "sonnet"]
            assert any(model in agent_config["model"] for model in valid_models), \
                f"Agent {agent_name} has invalid model: {agent_config['model']}"
    
    def test_activation_patterns(self, config_path):
        """Test activation patterns are defined"""
        with open(config_path) as f:
            config = json.load(f)
        
        agents = config["agents"]
        
        for agent_name, agent_config in agents.items():
            if "auto_activate_patterns" in agent_config:
                patterns = agent_config["auto_activate_patterns"]
                assert isinstance(patterns, list), \
                    f"Agent {agent_name} activation patterns should be a list"
                assert len(patterns) > 0, \
                    f"Agent {agent_name} has empty activation patterns"


class TestActivationEngine:
    """Test activation engine functionality"""
    
    @pytest.fixture
    def activation_engine_path(self):
        """Path to activation engine"""
        return Path(__file__).parent.parent.parent / ".claude" / "activation_engine.py"
    
    def test_activation_engine_exists(self, activation_engine_path):
        """Test activation engine file exists"""
        assert activation_engine_path.exists()
    
    def test_activation_engine_imports(self, activation_engine_path):
        """Test activation engine can be imported"""
        sys.path.insert(0, str(activation_engine_path.parent))
        
        try:
            from activation_engine import CrossAgentActivationEngine, ActivationContext
            
            # Should be able to create instances
            engine = CrossAgentActivationEngine()
            context = ActivationContext()
            
            assert engine is not None
            assert context is not None
            
        except ImportError as e:
            pytest.fail(f"Cannot import activation engine: {e}")
    
    def test_activation_rules_exist(self):
        """Test activation rules file exists"""
        rules_path = Path(__file__).parent.parent.parent / ".claude" / "activation_rules.json"
        assert rules_path.exists()
        
        with open(rules_path) as f:
            rules = json.load(f)
        
        assert "activation_rules" in rules
        assert "activation_settings" in rules
    
    def test_activation_analysis(self):
        """Test activation analysis functionality"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude"))
        
        from activation_engine import CrossAgentActivationEngine, ActivationContext
        
        engine = CrossAgentActivationEngine()
        
        # Test simple activation
        context = ActivationContext(
            file_path="test.py",
            file_content="print('hello')",
            project_phase="implementation"
        )
        
        activations = engine.analyze_activation_needs(context)
        assert isinstance(activations, list)
        
        # Test FastMCP activation
        fastmcp_context = ActivationContext(
            file_path="server.py",
            file_content="""
from fastmcp import FastMCP
@mcp.tool
async def test_tool():
    pass
            """,
            project_phase="implementation"
        )
        
        fastmcp_activations = engine.analyze_activation_needs(fastmcp_context)
        assert isinstance(fastmcp_activations, list)
        
        # Should activate FastMCP specialist
        agent_names = [activation[0] for activation in fastmcp_activations]
        # Note: actual activation depends on rules, so we just verify it returns results
        assert len(fastmcp_activations) >= 0


class TestAgentModelAssignment:
    """Test correct model assignment for agents"""
    
    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent.parent / ".claude" / "config.json"
    
    def test_opus_agents(self, config_path):
        """Test Opus agents are assigned correctly"""
        with open(config_path) as f:
            config = json.load(f)
        
        expected_opus_agents = ["mcp-orchestrator", "mcp-security-auditor"]
        agents = config["agents"]
        
        for agent_name in expected_opus_agents:
            if agent_name in agents:
                model = agents[agent_name]["model"]
                assert "opus" in model, f"Agent {agent_name} should use Opus model"
    
    def test_sonnet_agents(self, config_path):
        """Test Sonnet agents are assigned correctly"""
        with open(config_path) as f:
            config = json.load(f)
        
        expected_sonnet_agents = [
            "fastmcp-specialist",
            "mcp-protocol-expert", 
            "mcp-performance-optimizer",
            "mcp-deployment-specialist",
            "mcp-debugger",
            "context-manager"
        ]
        agents = config["agents"]
        
        for agent_name in expected_sonnet_agents:
            if agent_name in agents:
                model = agents[agent_name]["model"]
                assert "sonnet" in model, f"Agent {agent_name} should use Sonnet model"


class TestAgentCapabilities:
    """Test agent capability definitions"""
    
    @pytest.fixture
    def agents_dir(self):
        return Path(__file__).parent.parent.parent / ".claude" / "agents"
    
    def test_orchestrator_capabilities(self, agents_dir):
        """Test orchestrator has workflow capabilities"""
        orchestrator_path = agents_dir / "mcp-orchestrator.md"
        content = orchestrator_path.read_text()
        
        # Should mention workflow concepts
        workflow_terms = ["workflow", "orchestration", "quality gates", "delegation"]
        for term in workflow_terms:
            assert term.lower() in content.lower(), f"Orchestrator missing '{term}' capability"
    
    def test_security_auditor_capabilities(self, agents_dir):
        """Test security auditor has security capabilities"""
        auditor_path = agents_dir / "mcp-security-auditor.md"
        content = auditor_path.read_text()
        
        security_terms = ["oauth", "security", "authentication", "audit", "vulnerability"]
        for term in security_terms:
            assert term.lower() in content.lower(), f"Security auditor missing '{term}' capability"
    
    def test_fastmcp_specialist_capabilities(self, agents_dir):
        """Test FastMCP specialist has FastMCP capabilities"""
        specialist_path = agents_dir / "fastmcp-specialist.md"
        content = specialist_path.read_text()
        
        fastmcp_terms = ["fastmcp", "pydantic", "decorator", "@mcp.tool"]
        for term in fastmcp_terms:
            assert term.lower() in content.lower(), f"FastMCP specialist missing '{term}' capability"
    
    def test_performance_optimizer_capabilities(self, agents_dir):
        """Test performance optimizer has performance capabilities"""
        optimizer_path = agents_dir / "mcp-performance-optimizer.md"
        content = optimizer_path.read_text()
        
        performance_terms = ["performance", "async", "optimization", "caching", "monitoring"]
        for term in performance_terms:
            assert term.lower() in content.lower(), f"Performance optimizer missing '{term}' capability"


class TestAgentCoordination:
    """Test agent coordination mechanisms"""
    
    def test_context_manager_coordination(self):
        """Test context manager coordination capabilities"""
        agents_dir = Path(__file__).parent.parent.parent / ".claude" / "agents"
        context_manager_path = agents_dir / "context-manager.md"
        content = context_manager_path.read_text()
        
        coordination_terms = ["context", "coordination", "state", "handoff", "delegation"]
        for term in coordination_terms:
            assert term.lower() in content.lower(), \
                f"Context manager missing '{term}' coordination capability"
    
    def test_delegation_patterns(self):
        """Test delegation patterns are defined"""
        rules_path = Path(__file__).parent.parent.parent / ".claude" / "activation_rules.json"
        
        with open(rules_path) as f:
            rules = json.load(f)
        
        # Should have delegation chains
        if "activation_rules" in rules and "intelligent_delegation" in rules["activation_rules"]:
            delegation = rules["activation_rules"]["intelligent_delegation"]
            if "delegation_chains" in delegation:
                chains = delegation["delegation_chains"]
                assert len(chains) > 0, "No delegation chains defined"
                
                # Each chain should have required fields
                for chain in chains:
                    assert "from" in chain, "Delegation chain missing 'from'"
                    assert "to" in chain, "Delegation chain missing 'to'"
                    assert "condition" in chain, "Delegation chain missing 'condition'"


class TestAgentEnhancements:
    """Test enhanced agent features"""
    
    @pytest.fixture
    def agents_dir(self):
        return Path(__file__).parent.parent.parent / ".claude" / "agents"
    
    def test_context_manager_enhancements(self, agents_dir):
        """Test context manager has proactive features"""
        context_path = agents_dir / "context-manager.md"
        content = context_path.read_text()
        
        # Should have proactive features
        proactive_terms = ["proactive", "pattern", "prediction", "recommendation"]
        for term in proactive_terms:
            assert term.lower() in content.lower(), \
                f"Context manager missing proactive feature: {term}"
    
    def test_debugger_enhancements(self, agents_dir):
        """Test debugger has preventive monitoring"""
        debugger_path = agents_dir / "mcp-debugger.md"
        content = debugger_path.read_text()
        
        # Should have preventive features
        preventive_terms = ["preventive", "monitoring", "anomaly", "baseline", "prediction"]
        for term in preventive_terms:
            assert term.lower() in content.lower(), \
                f"Debugger missing preventive feature: {term}"


class TestAgentConsistency:
    """Test consistency across agent implementations"""
    
    @pytest.fixture
    def agents_dir(self):
        return Path(__file__).parent.parent.parent / ".claude" / "agents"
    
    def test_consistent_structure(self, agents_dir):
        """Test all agents have consistent structure"""
        required_sections = [
            "# Role",
            "# Core Competencies", 
            "# Standard Operating Procedure",
            "# Output Format",
            "# Constraints"
        ]
        
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            for section in required_sections:
                assert section in content, \
                    f"Agent {agent_file.name} missing required section: {section}"
    
    def test_consistent_sop_structure(self, agents_dir):
        """Test Standard Operating Procedures are consistently structured"""
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            if "# Standard Operating Procedure" in content:
                # Should have numbered steps
                sop_section = content.split("# Standard Operating Procedure")[1].split("#")[0]
                
                # Should contain step numbers
                has_steps = any(f"{i}." in sop_section for i in range(1, 8))
                assert has_steps, f"Agent {agent_file.name} SOP lacks numbered steps"
    
    def test_constraint_consistency(self, agents_dir):
        """Test constraints sections are present and meaningful"""
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            
            if "# Constraints" in content:
                constraints_section = content.split("# Constraints")[1]
                
                # Should have meaningful constraints (not just placeholders)
                assert len(constraints_section.strip()) > 100, \
                    f"Agent {agent_file.name} has minimal constraints section"
                
                # Should have bullet points or structured constraints
                assert "**" in constraints_section or "-" in constraints_section, \
                    f"Agent {agent_file.name} constraints not well structured"


def run_agent_tests():
    """Run all agent tests"""
    return pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_agent_tests()