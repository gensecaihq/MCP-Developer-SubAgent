"""
Quality gate system for ensuring standards compliance
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging
import time
import re
import ast
import json

logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Quality gate status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class GateResult:
    """Result of quality gate evaluation"""
    gate_name: str
    status: GateStatus
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    recommendations: List[str]
    execution_time: float
    critical_issues: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.critical_issues is None:
            self.critical_issues = []
        if self.warnings is None:
            self.warnings = []


class QualityGate(ABC):
    """Abstract base class for quality gates"""
    
    def __init__(self, name: str, weight: float = 1.0, critical: bool = False):
        self.name = name
        self.weight = weight  # Weight in overall score calculation
        self.critical = critical  # If true, failure stops pipeline
        
    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate the quality gate"""
        pass
    
    def _create_result(self, status: GateStatus, score: float, details: Dict[str, Any], 
                      recommendations: List[str], start_time: float,
                      critical_issues: List[str] = None, warnings: List[str] = None) -> GateResult:
        """Create a gate result with common fields"""
        return GateResult(
            gate_name=self.name,
            status=status,
            score=score,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time,
            critical_issues=critical_issues or [],
            warnings=warnings or []
        )


class PlanningGate(QualityGate):
    """Validates planning and architecture phase"""
    
    def __init__(self):
        super().__init__("planning", weight=3.0, critical=True)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Check for essential planning artifacts
        has_requirements = bool(context.get("requirements"))
        has_architecture = bool(context.get("architecture"))
        has_transport = bool(context.get("transport_selection"))
        has_tools_defined = bool(context.get("tools"))
        has_security_plan = bool(context.get("security_design"))
        
        checks = [
            has_requirements,
            has_architecture,
            has_transport,
            has_tools_defined,
            has_security_plan
        ]
        
        score = sum(checks) / len(checks)
        
        details = {
            "requirements_defined": has_requirements,
            "architecture_designed": has_architecture,
            "transport_selected": has_transport,
            "tools_planned": has_tools_defined,
            "security_planned": has_security_plan
        }
        
        recommendations = []
        critical_issues = []
        
        if not has_requirements:
            critical_issues.append("Requirements must be defined before proceeding")
        if not has_architecture:
            critical_issues.append("System architecture must be designed")
        if not has_transport:
            recommendations.append("Select appropriate transport layer (stdio, HTTP, SSE)")
        if not has_tools_defined:
            recommendations.append("Define MCP tools and their interfaces")
        if not has_security_plan:
            recommendations.append("Create security design for authentication/authorization")
        
        status = GateStatus.PASSED if score >= 0.8 else GateStatus.FAILED
        if critical_issues:
            status = GateStatus.FAILED
        
        return self._create_result(status, score, details, recommendations, start_time, critical_issues)


class ProtocolGate(QualityGate):
    """Validates MCP protocol compliance"""
    
    def __init__(self):
        super().__init__("protocol", weight=3.0, critical=True)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Check protocol compliance
        has_jsonrpc = self._check_jsonrpc_compliance(context)
        has_mcp_methods = self._check_mcp_methods(context)
        has_capability_negotiation = self._check_capabilities(context)
        has_error_handling = self._check_error_handling(context)
        
        checks = [has_jsonrpc, has_mcp_methods, has_capability_negotiation, has_error_handling]
        score = sum(checks) / len(checks)
        
        details = {
            "jsonrpc_compliant": has_jsonrpc,
            "mcp_methods_implemented": has_mcp_methods,
            "capability_negotiation": has_capability_negotiation,
            "error_handling": has_error_handling
        }
        
        recommendations = []
        if not has_jsonrpc:
            recommendations.append("Ensure JSON-RPC 2.0 compliance for all methods")
        if not has_mcp_methods:
            recommendations.append("Implement required MCP methods (initialize, tools/list, etc.)")
        if not has_capability_negotiation:
            recommendations.append("Add proper capability negotiation in initialize method")
        if not has_error_handling:
            recommendations.append("Implement comprehensive error handling with proper codes")
        
        status = GateStatus.PASSED if score >= 0.9 else GateStatus.FAILED
        
        return self._create_result(status, score, details, recommendations, start_time)
    
    def _check_jsonrpc_compliance(self, context: Dict[str, Any]) -> bool:
        """Check JSON-RPC 2.0 compliance"""
        code = context.get("code", "")
        # Look for JSON-RPC version handling
        return '"jsonrpc": "2.0"' in code or 'jsonrpc.*2\.0' in code
    
    def _check_mcp_methods(self, context: Dict[str, Any]) -> bool:
        """Check for required MCP methods"""
        code = context.get("code", "")
        required_methods = ["initialize", "tools/list", "tools/call"]
        return all(method in code for method in required_methods)
    
    def _check_capabilities(self, context: Dict[str, Any]) -> bool:
        """Check capability negotiation"""
        code = context.get("code", "")
        return "capabilities" in code and "protocolVersion" in code
    
    def _check_error_handling(self, context: Dict[str, Any]) -> bool:
        """Check error handling implementation"""
        code = context.get("code", "")
        return "except" in code or "try:" in code


class SecurityGate(QualityGate):
    """Validates security implementation"""
    
    def __init__(self):
        super().__init__("security", weight=2.5, critical=True)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Security checks
        has_input_validation = self._check_input_validation(context)
        has_auth_implementation = self._check_authentication(context)
        has_secure_patterns = self._check_secure_patterns(context)
        no_security_issues = self._check_security_issues(context)
        
        checks = [has_input_validation, has_auth_implementation, has_secure_patterns, no_security_issues]
        score = sum(checks) / len(checks)
        
        details = {
            "input_validation": has_input_validation,
            "authentication": has_auth_implementation,
            "secure_patterns": has_secure_patterns,
            "security_issues_found": not no_security_issues
        }
        
        recommendations = []
        critical_issues = []
        
        if not has_input_validation:
            critical_issues.append("Input validation is required for all user inputs")
        if not has_auth_implementation:
            recommendations.append("Implement proper authentication mechanism")
        if not has_secure_patterns:
            recommendations.append("Follow secure coding patterns")
        if not no_security_issues:
            critical_issues.append("Security vulnerabilities detected in code")
        
        status = GateStatus.PASSED if score >= 0.8 and not critical_issues else GateStatus.FAILED
        
        return self._create_result(status, score, details, recommendations, start_time, critical_issues)
    
    def _check_input_validation(self, context: Dict[str, Any]) -> bool:
        """Check for input validation"""
        code = context.get("code", "")
        validation_patterns = [
            r"Field\(.*validation.*\)",
            r"validator\(",
            r"validate_.*\(",
            r"if.*len\(.*\)",
            r"if.*isinstance\("
        ]
        return any(re.search(pattern, code, re.IGNORECASE) for pattern in validation_patterns)
    
    def _check_authentication(self, context: Dict[str, Any]) -> bool:
        """Check authentication implementation"""
        code = context.get("code", "")
        auth_patterns = ["oauth", "jwt", "token", "authenticate", "authorize"]
        return any(pattern in code.lower() for pattern in auth_patterns)
    
    def _check_secure_patterns(self, context: Dict[str, Any]) -> bool:
        """Check for secure coding patterns"""
        code = context.get("code", "")
        # Look for secure patterns like password hashing, secure random, etc.
        secure_patterns = ["secrets.", "hashlib", "bcrypt", "scrypt"]
        return any(pattern in code for pattern in secure_patterns)
    
    def _check_security_issues(self, context: Dict[str, Any]) -> bool:
        """Check for common security issues"""
        code = context.get("code", "")
        # Look for dangerous patterns
        dangerous_patterns = [
            r"eval\(",
            r"exec\(",
            r"os\.system",
            r"subprocess.*shell=True",
            r"pickle\.loads",
            r"yaml\.load\("
        ]
        return not any(re.search(pattern, code) for pattern in dangerous_patterns)


class ImplementationGate(QualityGate):
    """Validates implementation quality"""
    
    def __init__(self):
        super().__init__("implementation", weight=2.0, critical=False)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Implementation quality checks
        has_type_hints = self._check_type_hints(context)
        has_docstrings = self._check_docstrings(context)
        has_error_handling = self._check_error_handling(context)
        follows_patterns = self._check_fastmcp_patterns(context)
        is_syntactically_valid = self._check_syntax(context)
        
        checks = [has_type_hints, has_docstrings, has_error_handling, follows_patterns, is_syntactically_valid]
        score = sum(checks) / len(checks)
        
        details = {
            "type_hints": has_type_hints,
            "docstrings": has_docstrings,
            "error_handling": has_error_handling,
            "fastmcp_patterns": follows_patterns,
            "syntax_valid": is_syntactically_valid
        }
        
        recommendations = []
        warnings = []
        
        if not has_type_hints:
            warnings.append("Add type hints for better code maintainability")
        if not has_docstrings:
            warnings.append("Add docstrings to improve code documentation")
        if not has_error_handling:
            recommendations.append("Add comprehensive error handling")
        if not follows_patterns:
            recommendations.append("Follow FastMCP patterns and conventions")
        if not is_syntactically_valid:
            recommendations.append("Fix syntax errors in code")
        
        status = GateStatus.PASSED if score >= 0.6 else GateStatus.FAILED
        if not is_syntactically_valid:
            status = GateStatus.FAILED
        
        return self._create_result(status, score, details, recommendations, start_time, warnings=warnings)
    
    def _check_type_hints(self, context: Dict[str, Any]) -> bool:
        """Check for type hints"""
        code = context.get("code", "")
        return ": " in code and ("Dict[" in code or "List[" in code or "Optional[" in code)
    
    def _check_docstrings(self, context: Dict[str, Any]) -> bool:
        """Check for docstrings"""
        code = context.get("code", "")
        return '"""' in code or "'''" in code
    
    def _check_error_handling(self, context: Dict[str, Any]) -> bool:
        """Check error handling"""
        code = context.get("code", "")
        return "try:" in code and "except" in code
    
    def _check_fastmcp_patterns(self, context: Dict[str, Any]) -> bool:
        """Check FastMCP patterns"""
        code = context.get("code", "")
        return "@mcp.tool" in code or "@mcp.resource" in code or "FastMCP" in code
    
    def _check_syntax(self, context: Dict[str, Any]) -> bool:
        """Check syntax validity"""
        code = context.get("code", "")
        if not code:
            return False
        
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


class TestingGate(QualityGate):
    """Validates testing implementation"""
    
    def __init__(self):
        super().__init__("testing", weight=1.5, critical=False)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Testing checks
        has_tests = self._check_tests(context)
        has_test_coverage = self._check_coverage(context)
        tests_pass = self._check_test_results(context)
        
        checks = [has_tests, has_test_coverage, tests_pass]
        score = sum(checks) / len(checks)
        
        details = {
            "tests_present": has_tests,
            "test_coverage": has_test_coverage,
            "tests_passing": tests_pass
        }
        
        recommendations = []
        if not has_tests:
            recommendations.append("Add unit tests for MCP server functionality")
        if not has_test_coverage:
            recommendations.append("Ensure adequate test coverage (>80%)")
        if not tests_pass:
            recommendations.append("Fix failing tests before proceeding")
        
        status = GateStatus.PASSED if score >= 0.7 else GateStatus.WARNING
        
        return self._create_result(status, score, details, recommendations, start_time)
    
    def _check_tests(self, context: Dict[str, Any]) -> bool:
        """Check if tests exist"""
        return bool(context.get("tests")) or bool(context.get("test_results"))
    
    def _check_coverage(self, context: Dict[str, Any]) -> bool:
        """Check test coverage"""
        coverage = context.get("test_coverage", 0)
        return coverage >= 0.8
    
    def _check_test_results(self, context: Dict[str, Any]) -> bool:
        """Check if tests pass"""
        test_results = context.get("test_results", {})
        return test_results.get("passed", 0) > test_results.get("failed", 1)


class PerformanceGate(QualityGate):
    """Validates performance characteristics"""
    
    def __init__(self):
        super().__init__("performance", weight=1.0, critical=False)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Performance checks
        has_async_patterns = self._check_async_patterns(context)
        has_optimization = self._check_optimization(context)
        meets_benchmarks = self._check_benchmarks(context)
        
        checks = [has_async_patterns, has_optimization, meets_benchmarks]
        score = sum(checks) / len(checks)
        
        details = {
            "async_patterns": has_async_patterns,
            "optimization_present": has_optimization,
            "benchmarks_met": meets_benchmarks
        }
        
        recommendations = []
        if not has_async_patterns:
            recommendations.append("Use async/await patterns for better performance")
        if not has_optimization:
            recommendations.append("Add performance optimizations (caching, pooling)")
        if not meets_benchmarks:
            recommendations.append("Optimize to meet performance benchmarks")
        
        status = GateStatus.PASSED if score >= 0.6 else GateStatus.WARNING
        
        return self._create_result(status, score, details, recommendations, start_time)
    
    def _check_async_patterns(self, context: Dict[str, Any]) -> bool:
        """Check for async patterns"""
        code = context.get("code", "")
        return "async def" in code and "await" in code
    
    def _check_optimization(self, context: Dict[str, Any]) -> bool:
        """Check for optimization patterns"""
        code = context.get("code", "")
        optimization_patterns = ["cache", "pool", "optimize", "@lru_cache"]
        return any(pattern in code.lower() for pattern in optimization_patterns)
    
    def _check_benchmarks(self, context: Dict[str, Any]) -> bool:
        """Check performance benchmarks"""
        performance = context.get("performance_metrics", {})
        response_time = performance.get("avg_response_time", 0)
        return response_time < 1.0  # Less than 1 second


class DocumentationGate(QualityGate):
    """Validates documentation quality"""
    
    def __init__(self):
        super().__init__("documentation", weight=1.0, critical=False)
    
    async def evaluate(self, context: Dict[str, Any]) -> GateResult:
        start_time = time.time()
        
        # Documentation checks
        has_readme = self._check_readme(context)
        has_api_docs = self._check_api_docs(context)
        has_examples = self._check_examples(context)
        
        checks = [has_readme, has_api_docs, has_examples]
        score = sum(checks) / len(checks)
        
        details = {
            "readme_present": has_readme,
            "api_documentation": has_api_docs,
            "examples_provided": has_examples
        }
        
        recommendations = []
        if not has_readme:
            recommendations.append("Create comprehensive README with usage instructions")
        if not has_api_docs:
            recommendations.append("Document API endpoints and tool schemas")
        if not has_examples:
            recommendations.append("Provide usage examples and tutorials")
        
        status = GateStatus.PASSED if score >= 0.7 else GateStatus.WARNING
        
        return self._create_result(status, score, details, recommendations, start_time)
    
    def _check_readme(self, context: Dict[str, Any]) -> bool:
        """Check for README"""
        return bool(context.get("readme")) or bool(context.get("documentation"))
    
    def _check_api_docs(self, context: Dict[str, Any]) -> bool:
        """Check for API documentation"""
        code = context.get("code", "")
        return '"""' in code and ("Args:" in code or "Returns:" in code)
    
    def _check_examples(self, context: Dict[str, Any]) -> bool:
        """Check for examples"""
        return bool(context.get("examples")) or bool(context.get("usage_examples"))


class QualityGateManager:
    """Manages quality gate execution"""
    
    def __init__(self):
        self.gates = {
            "planning": PlanningGate(),
            "protocol": ProtocolGate(),
            "security": SecurityGate(),
            "implementation": ImplementationGate(),
            "testing": TestingGate(),
            "performance": PerformanceGate(),
            "documentation": DocumentationGate()
        }
        
        # Define gate execution order
        self.execution_order = [
            "planning",
            "protocol", 
            "security",
            "implementation",
            "testing",
            "performance",
            "documentation"
        ]
    
    async def run_gates(self, context: Dict[str, Any], 
                       gates_to_run: Optional[List[str]] = None,
                       stop_on_critical_failure: bool = True) -> Dict[str, GateResult]:
        """Run specified quality gates"""
        gates_to_run = gates_to_run or self.execution_order
        results = {}
        
        logger.info(f"Running quality gates: {gates_to_run}")
        
        for gate_name in gates_to_run:
            if gate_name not in self.gates:
                logger.warning(f"Unknown gate: {gate_name}")
                continue
            
            logger.info(f"Executing gate: {gate_name}")
            gate = self.gates[gate_name]
            
            try:
                result = await gate.evaluate(context)
                results[gate_name] = result
                
                logger.info(f"Gate {gate_name}: {result.status.value} (score: {result.score:.2f})")
                
                # Stop on critical failure
                if (stop_on_critical_failure and 
                    gate.critical and 
                    result.status == GateStatus.FAILED):
                    logger.error(f"Critical gate {gate_name} failed, stopping execution")
                    break
                    
            except Exception as e:
                logger.error(f"Gate {gate_name} execution failed: {e}")
                results[gate_name] = GateResult(
                    gate_name=gate_name,
                    status=GateStatus.FAILED,
                    score=0.0,
                    details={"error": str(e)},
                    recommendations=[f"Fix gate execution error: {str(e)}"],
                    execution_time=0.0,
                    critical_issues=[f"Gate execution failed: {str(e)}"]
                )
        
        return results
    
    def calculate_overall_score(self, results: Dict[str, GateResult]) -> float:
        """Calculate weighted overall score"""
        total_weight = 0.0
        weighted_score = 0.0
        
        for gate_name, result in results.items():
            if gate_name in self.gates:
                gate = self.gates[gate_name]
                total_weight += gate.weight
                weighted_score += result.score * gate.weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def get_gate_summary(self, results: Dict[str, GateResult]) -> Dict[str, Any]:
        """Get summary of gate results"""
        total_gates = len(results)
        passed_gates = sum(1 for r in results.values() if r.status == GateStatus.PASSED)
        failed_gates = sum(1 for r in results.values() if r.status == GateStatus.FAILED)
        warning_gates = sum(1 for r in results.values() if r.status == GateStatus.WARNING)
        
        overall_score = self.calculate_overall_score(results)
        
        all_recommendations = []
        all_critical_issues = []
        
        for result in results.values():
            all_recommendations.extend(result.recommendations)
            all_critical_issues.extend(result.critical_issues)
        
        return {
            "total_gates": total_gates,
            "passed": passed_gates,
            "failed": failed_gates,
            "warnings": warning_gates,
            "overall_score": overall_score,
            "success_rate": passed_gates / total_gates if total_gates > 0 else 0.0,
            "recommendations": list(set(all_recommendations)),
            "critical_issues": list(set(all_critical_issues)),
            "ready_for_production": failed_gates == 0 and len(all_critical_issues) == 0
        }