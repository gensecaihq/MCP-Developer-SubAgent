# Enterprise MCP Server with OAuth 2.1 Authentication

Enterprise-grade MCP server implementation demonstrating advanced security patterns with OAuth 2.1, JWT validation, and enterprise compliance features.

## Features

- **OAuth 2.1 with PKCE**: Full OAuth 2.1 flow implementation with PKCE security
- **Resource Indicators (RFC 8707)**: Compliant resource indicator handling
- **JWT Token Validation**: Comprehensive JWT processing with scope management
- **Security Audit Logging**: Enterprise-grade audit trail and security events
- **Rate Limiting**: DoS protection and request throttling
- **Scope-Based Access Control**: Fine-grained permission management

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   python server.py --port 8000 --auth-endpoint https://auth.company.com
   ```

3. **Configure Claude Desktop**:
   Add to your MCP client configuration:
   ```json
   {
     "mcp": {
       "servers": {
         "enterprise-server": {
           "command": "python",
           "args": ["/path/to/server.py", "--port", "8000"],
           "transport": "stdio",
           "env": {
             "OAUTH_CLIENT_ID": "your-client-id",
             "OAUTH_CLIENT_SECRET": "your-client-secret"
           }
         }
       }
     }
   }
   ```

## Security Features

### OAuth 2.1 Implementation
- PKCE (Proof Key for Code Exchange) support
- State parameter validation
- Secure token exchange flows
- Refresh token rotation

### JWT Validation
- RS256/ES256 signature verification
- Audience and issuer validation
- Scope-based authorization
- Token expiration handling

### Enterprise Compliance
- Comprehensive audit logging
- Rate limiting and DoS protection
- Input validation and sanitization
- Secure error handling

## Available Tools

### `secure_data_query`
Query enterprise data with scope-based access control:
- Requires `data:read` scope
- Audit logging for all access
- Input validation and sanitization

### `admin_operation`
Administrative operations with elevated permissions:
- Requires `admin:write` scope
- Multi-factor authentication validation
- Comprehensive audit trail

## Authentication Flow

1. **Authorization Request**: Client initiates OAuth 2.1 flow
2. **PKCE Challenge**: Server validates code challenge
3. **Token Exchange**: Secure token issuance with resource indicators
4. **API Access**: JWT-validated requests with scope checking
5. **Audit Logging**: Complete security event tracking

## Enterprise Integration

### Directory Services
- LDAP/Active Directory integration
- Group-based authorization
- Role mapping and inheritance

### Monitoring & Observability
- Security event correlation
- Performance metrics
- Compliance reporting

### Scalability
- Horizontal scaling support
- Session clustering
- Load balancer compatibility

## Security Considerations

### Input Validation
All inputs are validated using Pydantic models with:
- Type checking and coercion
- Length and format validation
- Injection attack prevention

### Rate Limiting
Configurable rate limits per:
- User identity
- Client application
- API endpoint

### Audit Requirements
Complete audit trail including:
- Authentication events
- Authorization decisions
- Data access patterns
- Security violations

## Next Steps

Use this enterprise server as a foundation for:
1. Integrating with corporate identity providers
2. Implementing custom authorization policies
3. Adding compliance-specific features
4. Scaling to production environments

For production deployment, consider:
- High availability configurations
- Database clustering
- Security monitoring integration
- Compliance validation tools