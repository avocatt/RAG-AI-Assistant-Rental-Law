# Security Configuration - RAG QA Rental Law Application

## Overview
This application uses a multi-layer security approach with Traefik Basic Authentication at the infrastructure level and API key validation at the application level.

## Architecture

```
Internet → Traefik Proxy (Basic Auth) → Protected Services
                ├── Backend API (port 8000) → API Key Validation
                └── Frontend UI (port 8501)
```

## Authentication Layers

### 1. Infrastructure Layer - Traefik Basic Authentication
Both frontend and backend services are protected by Traefik Basic Auth middleware, providing proxy-level security before requests reach the application.

#### Configuration in docker-compose.yaml:
```yaml
backend:
  labels:
    - traefik.http.middlewares.backend-auth.basicauth.users=${BASIC_AUTH_CREDENTIALS}
    - traefik.http.routers.backend.middlewares=backend-auth

frontend:
  labels:
    - traefik.http.middlewares.frontend-auth.basicauth.users=${BASIC_AUTH_CREDENTIALS}
    - traefik.http.routers.frontend.middlewares=frontend-auth
```

### 2. Application Layer - API Key Authentication
The backend FastAPI service implements additional API key validation for defense in depth:
- All API requests require `X-API-Key` header
- Rate limiting: 10 requests per minute per IP
- Validates against `API_SECRET_KEY` environment variable

## Setting Up Credentials

### Generate Basic Auth Credentials

#### Using htpasswd tool:
```bash
# Install htpasswd if not available
apt-get install apache2-utils  # Debian/Ubuntu
yum install httpd-tools         # RHEL/CentOS
brew install httpd              # macOS

# Generate credentials
htpasswd -nb username password
```

#### Using Docker (if htpasswd not available):
```bash
docker run --rm httpd:alpine htpasswd -nb username password
```

#### Using online generator:
For development only, you can use online htpasswd generators. Never use these for production passwords.

### Configure Environment Variables

#### Local Development (.env file):
```bash
# Basic Auth credentials (double $$ for docker-compose)
BASIC_AUTH_CREDENTIALS=username:$$apr1$$xxxxx$$yyyyyyyyyyyyy

# API Security
API_SECRET_KEY=your-secure-random-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

#### Coolify Production:
In Coolify's environment variables section:
1. Add `BASIC_AUTH_CREDENTIALS` with value: `username:$apr1$xxxxx$yyyyyyyyyyyyy` (single $ in Coolify)
2. Add `API_SECRET_KEY` with a secure random string
3. Add `OPENAI_API_KEY` with your OpenAI API key
4. Save and redeploy

### Multiple Users
To add multiple users, separate credentials with commas:
```bash
BASIC_AUTH_CREDENTIALS=admin:hash1,viewer:hash2,user:hash3
```

## Security Features

### Rate Limiting
- Backend API: 10 requests per minute per IP address
- Configurable in `main.py`:
  ```python
  RATE_LIMIT_REQUESTS = 10  # requests per minute
  RATE_LIMIT_WINDOW = 60    # seconds
  ```

### Logging
- Authentication failures logged with IP addresses
- Rate limit violations tracked
- API key validation attempts logged

### Health Checks
- Backend: `/health` endpoint for monitoring
- Frontend: Streamlit health endpoint

## Best Practices

### Password Requirements
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, and symbols
- Regular rotation (every 90 days recommended)

### Security Headers (Optional Enhancement)
Add to docker-compose.yaml for additional security:
```yaml
labels:
  - traefik.http.middlewares.security-headers.headers.stsSeconds=31536000
  - traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true
  - traefik.http.middlewares.security-headers.headers.stsPreload=true
  - traefik.http.routers.frontend.middlewares=frontend-auth,security-headers
```

### IP Whitelisting (Optional)
For restricted access environments:
```yaml
labels:
  - traefik.http.middlewares.ipwhitelist.ipwhitelist.sourcerange=10.0.0.0/8,192.168.0.0/16
  - traefik.http.routers.backend.middlewares=backend-auth,ipwhitelist
```

## Testing Authentication

### Command Line Testing
```bash
# Test without credentials (should return 401)
curl -I https://your-domain.com

# Test with credentials (should return 200)
curl -u username:password https://your-domain.com

# Test API with both Basic Auth and API Key
curl -u username:password \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -X POST https://your-api-domain.com/query \
     -d '{"query_text": "Test query"}'
```

### Browser Testing
1. Navigate to the application URL
2. Enter username and password when prompted
3. Credentials are cached until browser is closed

## Troubleshooting

### Common Issues

**401 Unauthorized despite correct credentials**
- Check for proper escaping of $ signs (use $$ in docker-compose)
- Verify environment variables are loaded correctly
- Ensure Traefik labels are applied (restart services)

**No authentication prompt appears**
- Verify Traefik is running and configured
- Check docker-compose labels are correct
- Ensure services have been redeployed after changes

**API Key errors after Basic Auth success**
- Verify API_SECRET_KEY is set in environment
- Check frontend is sending X-API-Key header
- Ensure API_SECRET_KEY matches between frontend and backend

**Rate limiting issues**
- Default: 10 requests per minute
- Check logs for rate limit violations
- Adjust RATE_LIMIT_REQUESTS if needed

## Migration Notes

### From Application-Level Password Protection
This application previously used Streamlit's built-in password protection. The migration to Traefik Basic Auth provides:
- Better security (proxy-level protection)
- Consistent authentication across services
- Simplified application code
- Standard HTTP authentication

### Removed Components
- Streamlit password checking logic (`check_password()` function)
- `DEMO_PASSWORD` environment variable
- Session-based password state management

### Retained Security Features
- API key validation for backend
- Rate limiting
- Security logging
- Input validation

## Future Enhancements

Consider these options for enhanced security:

1. **OAuth2/OIDC Integration**
   - Integrate with Auth0, Keycloak, or Google
   - Provides user management and SSO

2. **JWT Token Authentication**
   - Stateless authentication
   - Better for API-heavy applications

3. **mTLS (Mutual TLS)**
   - Certificate-based authentication
   - Ideal for machine-to-machine communication

4. **Fail2ban Integration**
   - Automatic IP blocking after failed attempts
   - Protection against brute force attacks

## Security Checklist

- [ ] Strong passwords configured (12+ characters)
- [ ] HTTPS enabled in production
- [ ] Environment variables properly secured
- [ ] Regular credential rotation scheduled
- [ ] Access logs monitored
- [ ] Rate limiting configured
- [ ] Health checks operational
- [ ] Backup authentication method available
- [ ] Security headers configured (optional)
- [ ] IP whitelisting considered (if applicable)