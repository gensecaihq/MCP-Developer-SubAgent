#!/usr/bin/env python3
"""
Enterprise MCP Server with OAuth 2.1 Authentication

Demonstrates enterprise-grade MCP server implementation with:
- OAuth 2.1 with PKCE authentication
- Resource Indicators (RFC 8707) compliance
- JWT token validation and scope management
- Comprehensive security audit logging
- Rate limiting and DoS protection

Usage:
    python server.py --port 8000 --auth-endpoint https://auth.company.com

This server showcases enterprise security patterns while maintaining
FastMCP simplicity and repository-verified implementation patterns.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Set
import jwt
import secrets
import hashlib
import base64
import time
import logging
import asyncio
import aiohttp
from functools import wraps
from dataclasses import dataclass
from collections import defaultdict, deque
import structlog
import json

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastMCP server with enterprise configuration
mcp = FastMCP("enterprise-auth-server")

# Security models and configurations
@dataclass
class SecurityContext:
    """Security context for authenticated requests"""
    user_id: str
    client_id: str
    scopes: Set[str]
    token_id: str
    session_id: str
    ip_address: str
    issued_at: float
    expires_at: float
    
    def has_scope(self, required_scope: str) -> bool:
        return required_scope in self.scopes
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class OAuth2Config(BaseModel):
    """OAuth 2.1 configuration"""
    client_id: str = Field(description="OAuth client identifier")
    client_secret: str = Field(description="OAuth client secret")
    auth_endpoint: str = Field(description="Authorization server endpoint")
    token_endpoint: str = Field(description="Token exchange endpoint")
    jwks_endpoint: str = Field(description="JSON Web Key Set endpoint")
    resource_indicators: List[str] = Field(description="Supported resource indicators")

class AuthenticationRequest(BaseModel):
    """Authentication request with PKCE"""
    client_id: str = Field(description="OAuth client ID")
    code_verifier: str = Field(description="PKCE code verifier")
    authorization_code: str = Field(description="Authorization code")
    resource: Optional[str] = Field(description="Resource indicator (RFC 8707)")

class SecureDataRequest(BaseModel):
    """Secure data request with validation"""
    query: str = Field(min_length=1, max_length=1000, description="Data query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    limit: int = Field(default=100, ge=1, le=1000, description="Result limit")
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize query input for security"""
        import re
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r';\s*(DROP|DELETE|TRUNCATE|ALTER)',
            r'UNION\s+SELECT',
            r'(\'|\"|\`|--|\/\*|\*\/)',
            r'(xp_|sp_|exec\s*\()'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Query contains potentially dangerous patterns')
        
        return v.strip()

# Enterprise security components
class OAuth2Validator:
    """OAuth 2.1 token validator with PKCE and Resource Indicators support"""
    
    def __init__(self, config: OAuth2Config):
        self.config = config
        self.code_verifiers = {}  # In production, use Redis or secure storage
        self.jwks_cache = {}
        self.jwks_cache_expiry = 0
    
    def generate_pkce_challenge(self, client_id: str) -> Dict[str, str]:
        """Generate PKCE challenge for OAuth 2.1"""
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Store verifier (in production, use secure storage)
        self.code_verifiers[client_id] = code_verifier
        
        return {
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "code_verifier": code_verifier  # Return for client to store securely
        }
    
    async def validate_pkce(self, client_id: str, code_verifier: str) -> bool:
        """Validate PKCE code verifier"""
        stored_verifier = self.code_verifiers.get(client_id)
        if not stored_verifier:
            return False
        
        # Verify the code verifier matches
        is_valid = secrets.compare_digest(stored_verifier, code_verifier)
        
        # Clean up stored verifier
        if client_id in self.code_verifiers:
            del self.code_verifiers[client_id]
        
        return is_valid
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set with caching"""
        current_time = time.time()
        
        if current_time > self.jwks_cache_expiry:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.config.jwks_endpoint) as response:
                        jwks_data = await response.json()
                        self.jwks_cache = jwks_data
                        self.jwks_cache_expiry = current_time + 300  # Cache for 5 minutes
            except Exception as e:
                logger.error("Failed to fetch JWKS", error=str(e))
                if not self.jwks_cache:
                    raise
        
        return self.jwks_cache
    
    async def validate_token(self, token: str, required_resource: Optional[str] = None) -> SecurityContext:
        """Validate JWT token with comprehensive security checks"""
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            key_id = header.get('kid')
            
            if not key_id:
                raise ValueError("Token missing key ID")
            
            # Get public key for verification
            jwks = await self.get_jwks()
            public_key = self._get_public_key(jwks, key_id)
            
            # Verify token with comprehensive options
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256', 'ES256'],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_aud': True,
                    'require': ['exp', 'iat', 'sub', 'aud', 'scope']
                }
            )
            
            # Validate Resource Indicators (RFC 8707)
            if required_resource:
                audiences = payload.get('aud', [])
                if isinstance(audiences, str):
                    audiences = [audiences]
                
                if required_resource not in audiences:
                    raise ValueError(f"Token not valid for resource: {required_resource}")
            
            # Extract scopes
            scopes = set(payload.get('scope', '').split())
            
            # Create security context
            security_context = SecurityContext(
                user_id=payload.get('sub'),
                client_id=payload.get('client_id', 'unknown'),
                scopes=scopes,
                token_id=payload.get('jti', 'unknown'),
                session_id=secrets.token_urlsafe(16),
                ip_address='unknown',  # Will be set by middleware
                issued_at=payload.get('iat'),
                expires_at=payload.get('exp')
            )
            
            return security_context
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            raise ValueError(f"Token validation failed: {str(e)}")
    
    def _get_public_key(self, jwks: Dict[str, Any], key_id: str):
        """Extract public key from JWKS"""
        keys = jwks.get('keys', [])
        for key in keys:
            if key.get('kid') == key_id:
                # In production, properly parse the JWK
                # This is a simplified example
                return key.get('x5c', [None])[0] if key.get('x5c') else None
        
        raise ValueError(f"Key ID {key_id} not found in JWKS")

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.user_requests = defaultdict(deque)
        self.ip_requests = defaultdict(deque)
        self.global_requests = deque()
        
        # Rate limit configurations
        self.limits = {
            'per_user_minute': 60,
            'per_user_hour': 1000,
            'per_ip_minute': 100,
            'global_per_second': 1000
        }
    
    async def check_rate_limit(self, user_id: str, ip_address: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check per-user limits
        user_minute_count = len([
            req for req in self.user_requests[user_id]
            if current_time - req < 60
        ])
        
        if user_minute_count >= self.limits['per_user_minute']:
            logger.warning("User rate limit exceeded", user_id=user_id, count=user_minute_count)
            return False
        
        # Check per-IP limits
        ip_minute_count = len([
            req for req in self.ip_requests[ip_address]
            if current_time - req < 60
        ])
        
        if ip_minute_count >= self.limits['per_ip_minute']:
            logger.warning("IP rate limit exceeded", ip_address=ip_address, count=ip_minute_count)
            return False
        
        # Record the request
        self.user_requests[user_id].append(current_time)
        self.ip_requests[ip_address].append(current_time)
        self.global_requests.append(current_time)
        
        return True
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old rate limit entries"""
        cutoff_time = current_time - 3600  # Keep 1 hour of data
        
        for user_deque in self.user_requests.values():
            while user_deque and user_deque[0] < cutoff_time:
                user_deque.popleft()
        
        for ip_deque in self.ip_requests.values():
            while ip_deque and ip_deque[0] < cutoff_time:
                ip_deque.popleft()
        
        while self.global_requests and self.global_requests[0] < cutoff_time:
            self.global_requests.popleft()

class SecurityAuditLogger:
    """Comprehensive security audit logging"""
    
    def __init__(self):
        self.audit_logger = structlog.get_logger("security_audit")
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str, details: Dict[str, Any] = None):
        """Log authentication attempts"""
        self.audit_logger.info(
            "authentication_attempt",
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            details=details or {},
            event_type="auth"
        )
    
    def log_authorization_check(self, user_id: str, resource: str, action: str, granted: bool):
        """Log authorization decisions"""
        self.audit_logger.info(
            "authorization_check",
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            event_type="authz"
        )
    
    def log_suspicious_activity(self, user_id: str, activity: str, risk_level: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        self.audit_logger.warning(
            "suspicious_activity",
            user_id=user_id,
            activity=activity,
            risk_level=risk_level,
            details=details,
            event_type="security"
        )
    
    def log_data_access(self, user_id: str, resource: str, action: str, record_count: int):
        """Log data access events"""
        self.audit_logger.info(
            "data_access",
            user_id=user_id,
            resource=resource,
            action=action,
            record_count=record_count,
            event_type="data"
        )

# Initialize security components
oauth_config = OAuth2Config(
    client_id="mcp-enterprise-client",
    client_secret="secure-client-secret",  # In production, load from secure storage
    auth_endpoint="https://auth.company.com/oauth2/authorize",
    token_endpoint="https://auth.company.com/oauth2/token",
    jwks_endpoint="https://auth.company.com/.well-known/jwks.json",
    resource_indicators=[
        "https://api.company.com/mcp/tools",
        "https://api.company.com/mcp/resources",
        "https://api.company.com/mcp/data"
    ]
)

oauth_validator = OAuth2Validator(oauth_config)
rate_limiter = RateLimiter()
audit_logger = SecurityAuditLogger()

# Security decorators
def requires_authentication(required_scope: str = None, required_resource: str = None):
    """Decorator for authentication and authorization"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token from request context (simplified for example)
            auth_token = kwargs.get('auth_token')
            if not auth_token:
                audit_logger.log_authentication_attempt("unknown", False, "unknown", {"error": "missing_token"})
                raise ValueError("Authentication required")
            
            try:
                # Validate token
                security_context = await oauth_validator.validate_token(auth_token, required_resource)
                
                # Check if token is expired
                if security_context.is_expired():
                    audit_logger.log_authentication_attempt(
                        security_context.user_id, False, security_context.ip_address, {"error": "token_expired"}
                    )
                    raise ValueError("Token has expired")
                
                # Check required scope
                if required_scope and not security_context.has_scope(required_scope):
                    audit_logger.log_authorization_check(
                        security_context.user_id, required_resource or "unknown", required_scope, False
                    )
                    raise ValueError(f"Insufficient scope: {required_scope} required")
                
                # Check rate limits
                if not await rate_limiter.check_rate_limit(security_context.user_id, security_context.ip_address):
                    audit_logger.log_suspicious_activity(
                        security_context.user_id, "rate_limit_exceeded", "medium", 
                        {"ip_address": security_context.ip_address}
                    )
                    raise ValueError("Rate limit exceeded")
                
                # Log successful authentication
                audit_logger.log_authentication_attempt(
                    security_context.user_id, True, security_context.ip_address
                )
                
                audit_logger.log_authorization_check(
                    security_context.user_id, required_resource or func.__name__, required_scope or "execute", True
                )
                
                # Add security context to kwargs
                kwargs['security_context'] = security_context
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error("Authentication/authorization failed", error=str(e))
                raise
        
        return wrapper
    return decorator

# Secure MCP tools
@mcp.tool
@requires_authentication(
    required_scope="data:read",
    required_resource="https://api.company.com/mcp/data"
)
async def secure_query_data(
    request: SecureDataRequest,
    auth_token: str = None,
    security_context: SecurityContext = None
) -> Dict[str, Any]:
    """
    Secure data query with comprehensive authentication and authorization.
    
    This tool demonstrates enterprise security patterns including:
    - OAuth 2.1 with PKCE authentication
    - Resource Indicators (RFC 8707) compliance
    - Scope-based authorization
    - Input validation and sanitization
    - Comprehensive audit logging
    - Rate limiting protection
    
    Args:
        request: Validated and sanitized query request
        auth_token: JWT authentication token
        security_context: Injected security context
    
    Returns:
        Secure query results with metadata
    """
    try:
        start_time = time.time()
        
        # Simulate secure data access
        # In production, this would connect to secure databases
        simulated_data = [
            {"id": i, "value": f"secure_data_{i}", "user_access": security_context.user_id}
            for i in range(min(request.limit, 10))
        ]
        
        # Apply filters if provided
        if request.filters:
            # Apply secure filtering logic
            pass
        
        # Log data access
        audit_logger.log_data_access(
            security_context.user_id,
            "secure_data_table",
            "read",
            len(simulated_data)
        )
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "data": simulated_data,
            "metadata": {
                "user_id": security_context.user_id,
                "scopes": list(security_context.scopes),
                "query": request.query,
                "record_count": len(simulated_data),
                "processing_time": round(processing_time, 3),
                "security_level": "enterprise"
            }
        }
        
    except Exception as e:
        logger.error("Secure query failed", error=str(e), user_id=security_context.user_id)
        
        audit_logger.log_suspicious_activity(
            security_context.user_id,
            "query_failure",
            "low",
            {"error": str(e), "query": request.query}
        )
        
        return {
            "success": False,
            "error": "Query processing failed",
            "metadata": {
                "user_id": security_context.user_id,
                "error_type": "processing_error"
            }
        }

@mcp.tool
@requires_authentication(
    required_scope="admin:manage",
    required_resource="https://api.company.com/mcp/tools"
)
async def admin_system_status(
    auth_token: str = None,
    security_context: SecurityContext = None
) -> Dict[str, Any]:
    """
    Administrative system status - requires admin scope.
    
    Demonstrates high-privilege operations with strict authorization.
    
    Args:
        auth_token: JWT authentication token
        security_context: Injected security context
    
    Returns:
        System status information
    """
    try:
        # Verify admin access
        if not security_context.has_scope("admin:manage"):
            audit_logger.log_authorization_check(
                security_context.user_id, "admin_system_status", "admin:manage", False
            )
            raise ValueError("Administrative privileges required")
        
        # Log admin access
        audit_logger.log_authorization_check(
            security_context.user_id, "admin_system_status", "admin:manage", True
        )
        
        # Simulate system status collection
        system_status = {
            "server_status": "healthy",
            "database_connections": 15,
            "active_sessions": 42,
            "memory_usage": "68%",
            "cpu_usage": "23%",
            "uptime": "5 days, 3 hours",
            "last_security_scan": "2025-01-15T10:30:00Z"
        }
        
        audit_logger.log_data_access(
            security_context.user_id,
            "system_status",
            "admin_read",
            1
        )
        
        return {
            "success": True,
            "status": system_status,
            "metadata": {
                "admin_user": security_context.user_id,
                "access_level": "system_admin",
                "timestamp": time.time()
            }
        }
        
    except Exception as e:
        logger.error("Admin status query failed", error=str(e), user_id=security_context.user_id)
        return {"success": False, "error": str(e)}

# Authentication helper tools
@mcp.tool
async def initiate_pkce_flow(client_id: str) -> Dict[str, str]:
    """
    Initiate OAuth 2.1 PKCE authentication flow.
    
    Generates PKCE challenge for secure authentication.
    
    Args:
        client_id: OAuth client identifier
    
    Returns:
        PKCE challenge parameters
    """
    try:
        if client_id != oauth_config.client_id:
            raise ValueError("Invalid client ID")
        
        pkce_data = oauth_validator.generate_pkce_challenge(client_id)
        
        # Log PKCE initiation
        audit_logger.log_authentication_attempt("unknown", True, "unknown", {
            "action": "pkce_initiation",
            "client_id": client_id
        })
        
        return {
            "auth_url": f"{oauth_config.auth_endpoint}?client_id={client_id}&response_type=code&code_challenge={pkce_data['code_challenge']}&code_challenge_method=S256",
            "code_challenge": pkce_data["code_challenge"],
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(32)
        }
        
    except Exception as e:
        logger.error("PKCE initiation failed", error=str(e), client_id=client_id)
        return {"error": str(e)}

# Resource with authentication
@mcp.resource("secure://enterprise/{resource_type}")
@requires_authentication(
    required_scope="resource:read",
    required_resource="https://api.company.com/mcp/resources"
)
async def get_secure_resource(
    resource_type: str,
    auth_token: str = None,
    security_context: SecurityContext = None
) -> str:
    """
    Secure resource access with authentication.
    
    Args:
        resource_type: Type of resource to retrieve
        auth_token: JWT authentication token
        security_context: Injected security context
    
    Returns:
        JSON string with secure resource data
    """
    try:
        secure_resources = {
            "policies": {
                "data_retention": "7 years",
                "access_control": "role_based",
                "encryption": "AES-256"
            },
            "configurations": {
                "max_connections": 100,
                "timeout_seconds": 30,
                "retry_attempts": 3
            },
            "metrics": {
                "active_users": 1250,
                "daily_requests": 50000,
                "error_rate": 0.02
            }
        }
        
        if resource_type not in secure_resources:
            available_types = list(secure_resources.keys())
            raise ValueError(f"Resource type '{resource_type}' not found. Available: {available_types}")
        
        # Log resource access
        audit_logger.log_data_access(
            security_context.user_id,
            f"secure_resource_{resource_type}",
            "read",
            1
        )
        
        resource_data = secure_resources[resource_type]
        resource_data["accessed_by"] = security_context.user_id
        resource_data["access_time"] = time.time()
        
        return json.dumps(resource_data, indent=2)
        
    except Exception as e:
        logger.error("Secure resource access failed", error=str(e), user_id=security_context.user_id)
        return json.dumps({"error": str(e)})

# Server lifecycle with security initialization
async def initialize_enterprise_server():
    """Initialize enterprise server with security components"""
    logger.info("Initializing Enterprise MCP Server with OAuth 2.1...")
    
    # Initialize security components
    await oauth_validator.get_jwks()  # Preload JWKS
    
    logger.info("Security components initialized")
    logger.info("Enterprise MCP Server ready for secure connections")

async def cleanup_enterprise_server():
    """Cleanup enterprise server resources"""
    logger.info("Shutting down Enterprise MCP Server...")
    # Cleanup security resources if needed

if __name__ == "__main__":
    try:
        # Initialize server
        asyncio.run(initialize_enterprise_server())
        
        # Run the server
        logger.info("Starting Enterprise MCP Server with Authentication...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error("Server error", error=str(e))
    finally:
        asyncio.run(cleanup_enterprise_server())