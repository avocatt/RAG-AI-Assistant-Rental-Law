# Coolify 4.0 Deployment Guide & Best Practices

*A comprehensive reference guide based on real-world deployment experience and troubleshooting*

## Table of Contents
- [Overview](#overview)
- [Core Principles](#core-principles)
- [Docker Compose Configuration](#docker-compose-configuration)
- [Common Issues & Solutions](#common-issues--solutions)
- [Multi-Service Deployment Setup](#multi-service-deployment-setup)
- [Environment Variables](#environment-variables)
- [Networking & Domains](#networking--domains)
- [Troubleshooting Checklist](#troubleshooting-checklist)
- [Migration from Older Versions](#migration-from-older-versions)

## Overview

Coolify 4.0 has evolved significantly from earlier versions, introducing a service-centric approach where infrastructure management is handled through the UI, while Docker Compose files focus purely on application logic.

**Key Philosophy:** Let Coolify handle infrastructure concerns (networking, SSL, routing) while your compose files define application structure.

## Core Principles

### ✅ DO These Things:
1. **Let Coolify manage container naming** - No `container_name` specifications
2. **Configure routing through Coolify UI** - No manual Traefik labels
3. **Use `expose` instead of `ports`** - Coolify handles port mapping
4. **Use Coolify Magic Variables** - Dynamic service discovery
5. **Keep compose files clean** - Focus on application logic only

### ❌ AVOID These Things:
1. **External network references** - Coolify manages networking per stack
2. **Port mappings in compose** - Can cause "port already allocated" errors
3. **Hardcoded URLs** - Use magic variables instead
4. **Custom container names** - Breaks rolling updates and scaling

### ⚠️ IMPORTANT LIMITATION:
**Manual Traefik labels ARE REQUIRED for custom domains** - Coolify only generates Traefik labels automatically for auto-generated domains (*.sslip.io), NOT for custom domains. See the "Custom Domain Labels" section below.

## Docker Compose Configuration

### Basic Template Structure

```yaml
version: '3.8'

services:
  # Database (if needed)
  postgres:
    image: postgres:15-alpine
    # NO container_name
    restart: unless-stopped
    environment:
      - POSTGRES_DB=myapp_db
      - POSTGRES_USER=${POSTGRES_USER:-myapp}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-myapp}"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    # NO container_name
    expose:
      - "8000"  # Use expose, NOT ports
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://${POSTGRES_USER:-myapp}:${POSTGRES_PASSWORD}@postgres:5432/myapp_db
      - FRONTEND_URL=${SERVICE_FQDN_FRONTEND}  # Magic variable
      # Add your app-specific env vars here
    volumes:
      - app_logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    # NO container_name
    expose:
      - "80"   # Use expose, NOT ports
    environment:
      - API_URL=${SERVICE_FQDN_BACKEND}  # Magic variable
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  app_logs:
    driver: local

# NO networks section - Coolify handles this
```

## Custom Domain Labels

⚠️ **CRITICAL:** If you use custom domains (not auto-generated *.sslip.io), you MUST add Traefik labels manually.

### Template for Custom Domain Services

```yaml
services:
  backend:
    build: ./backend
    expose:
      - "8000"
    environment:
      - FRONTEND_URL=${SERVICE_FQDN_FRONTEND}
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.gzip.compress=true"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
      # HTTPS Router
      - "traefik.http.routers.https-[unique-id]-backend.entryPoints=https"
      - "traefik.http.routers.https-[unique-id]-backend.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.https-[unique-id]-backend.tls=true"
      - "traefik.http.routers.https-[unique-id]-backend.tls.certresolver=letsencrypt"
      - "traefik.http.routers.https-[unique-id]-backend.middlewares=gzip"
      - "traefik.http.services.https-[unique-id]-backend.loadbalancer.server.port=8000"
      # HTTP to HTTPS Redirect
      - "traefik.http.routers.http-[unique-id]-backend.entryPoints=http"
      - "traefik.http.routers.http-[unique-id]-backend.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.http-[unique-id]-backend.middlewares=redirect-to-https"

  frontend:
    build: ./frontend
    expose:
      - "80"
    environment:
      - API_URL=${SERVICE_FQDN_BACKEND}
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.gzip.compress=true"
      # HTTPS Router  
      - "traefik.http.routers.https-[unique-id]-frontend.entryPoints=https"
      - "traefik.http.routers.https-[unique-id]-frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.https-[unique-id]-frontend.tls=true"
      - "traefik.http.routers.https-[unique-id]-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.routers.https-[unique-id]-frontend.middlewares=gzip"
      - "traefik.http.services.https-[unique-id]-frontend.loadbalancer.server.port=80"
      # HTTP to HTTPS Redirect
      - "traefik.http.routers.http-[unique-id]-frontend.entryPoints=http"
      - "traefik.http.routers.http-[unique-id]-frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.http-[unique-id]-frontend.middlewares=redirect-to-https"
```

### Important Notes:
- **Replace `[unique-id]`** with a short unique identifier (e.g., part of your app's UUID)
- **Router names must be unique** across your entire VPS
- **Both HTTP and HTTPS routers needed** for proper SSL redirect
- **Magic variables still work** for inter-service communication

## Common Issues & Solutions

### Issue: "No Available Server" Error
**Symptoms:** Containers are running and healthy, but domains return "no available server"

**Root Cause:** Traefik routing not configured properly - usually missing Traefik labels for custom domains

**Solutions:**

**Option 1: Use Auto-Generated Domains (Quick Fix)**
1. In Coolify UI, click "Generate Domain" for each service
2. Use the provided *.sslip.io domains temporarily
3. Coolify will automatically add Traefik labels

**Option 2: Add Manual Traefik Labels for Custom Domains (Recommended)**
1. Keep your custom domains in Coolify UI
2. Add Traefik labels to docker-compose.yml (see Custom Domain Labels section)
3. Ensure services use `expose` not `ports`
4. Redeploy the application

### Issue: Container Name Conflicts
**Symptoms:** "Container name already in use" errors

**Root Cause:** Multiple applications trying to use same container names

**Solution:**
1. Remove all `container_name` specifications
2. Let Coolify auto-generate names with UUIDs
3. Use magic variables for inter-service communication

### Issue: Rolling Updates Not Working
**Symptoms:** Deployments require downtime, no zero-downtime updates

**Root Cause:** Custom container names disable rolling updates

**Solution:**
1. Remove `container_name` from all services
2. Coolify will enable rolling updates automatically

### Issue: Port Binding Conflicts
**Symptoms:** "Port already allocated" errors during deployment

**Root Cause:** Multiple applications trying to bind to same host ports

**Solution:**
1. Use `expose` instead of `ports` in docker-compose.yml
2. Let Coolify handle port mapping through Traefik

## Multi-Service Deployment Setup

### Step 1: Prepare Docker Compose File
- Follow the template above
- Remove any existing Traefik labels
- Use magic variables for inter-service communication

### Step 2: Configure in Coolify UI
1. **Create New Resource** → **Docker Compose**
2. **Set Repository Details** (Git URL, branch, docker-compose path)
3. **Configure Each Service Individually:**
   
   **For Backend Service:**
   - Domain: `api.yourdomain.com` 
   - Port: `8000` (or your backend port)
   - Enable HTTPS: ✓
   
   **For Frontend Service:**
   - Domain: `yourdomain.com`
   - Port: `80` (or your frontend port)  
   - Enable HTTPS: ✓

### Step 3: Environment Variables
Set in Coolify UI **Environment Variables** tab:
```bash
# Database
POSTGRES_USER=myapp
POSTGRES_PASSWORD=secure_password_here

# App-specific variables
JWT_SECRET=your_jwt_secret
API_KEY=your_api_key

# Coolify will automatically provide:
# SERVICE_FQDN_BACKEND=https://api.yourdomain.com
# SERVICE_FQDN_FRONTEND=https://yourdomain.com
```

### Step 4: Advanced Configuration
In Coolify **Advanced** tab:
- **Auto Deploy**: ✓ (for Git-based deployments)
- **Force HTTPS**: ✓ (redirect HTTP to HTTPS)
- **Enable Gzip Compression**: ✓
- **Raw Compose Deployment**: ❌ (use Coolify's managed approach)

## Environment Variables

### Magic Variables (Coolify 4.0+)
Coolify automatically provides these environment variables:

- `SERVICE_FQDN_<SERVICE_NAME>` - Full domain URL for the service
- `SERVICE_URL_<SERVICE_NAME>` - Same as FQDN
- `SERVICE_USER_<SERVICE_NAME>` - Random username (if needed)
- `SERVICE_PASSWORD_<SERVICE_NAME>` - Random password (if needed)

**Service Name Rules:**
- Uppercase the service name from your docker-compose.yml
- Replace hyphens with underscores
- Example: `my-backend` becomes `SERVICE_FQDN_MY_BACKEND`

### Usage Examples:
```yaml
environment:
  # Instead of hardcoded URLs:
  - API_URL=https://api.mydomain.com  # ❌ DON'T
  
  # Use magic variables:
  - API_URL=${SERVICE_FQDN_BACKEND}   # ✅ DO
  - FRONTEND_URL=${SERVICE_FQDN_FRONTEND}
  - DATABASE_URL=postgresql://user:pass@postgres:5432/db
```

## Networking & Domains

### Domain Configuration Best Practices:
1. **Use subdomain pattern for APIs:** `api.yourdomain.com`
2. **Use main domain for frontend:** `yourdomain.com`
3. **Enable HTTPS for all services** - Coolify handles Let's Encrypt automatically
4. **DNS must point to your VPS IP** before deployment

### Cross-Stack Communication:
If you need services from different applications to communicate:
1. Enable **"Connect to Predefined Network"** in Advanced settings
2. Services will be renamed to `<service>-<uuid>` format
3. Update connection strings to use the UUID-suffixed names

### Internal vs External URLs:
- **Internal:** Services use service names directly (`http://backend:8000`)
- **External:** Use magic variables that resolve to full HTTPS URLs

## Troubleshooting Checklist

### Pre-Deployment Checklist:
- [ ] No `container_name` specifications in docker-compose.yml
- [ ] **If using custom domains:** Traefik labels added to docker-compose.yml
- [ ] **If using auto-generated domains:** No Traefik labels needed
- [ ] No `ports` mappings, only `expose` directives
- [ ] No external network configurations
- [ ] Magic variables used for inter-service communication
- [ ] Health checks defined for all services
- [ ] DNS records point to correct VPS IP

### Post-Deployment Verification:
```bash
# Check containers are running
docker ps | grep <app-name>

# Check container logs
docker logs <container-name>

# Test internal connectivity
docker exec <backend-container> curl http://localhost:8000/health

# Test external domains
curl -I https://yourdomain.com
curl -I https://api.yourdomain.com/health

# Check Traefik routing
docker logs coolify-proxy --tail 20
```

### Common Error Messages & Solutions:

**"Port already allocated"**
- Remove `ports` from docker-compose.yml, use `expose` only

**"Container name conflict"**  
- Remove `container_name` specifications

**"Service unavailable"**
- Check domain configuration in Coolify UI
- Verify DNS records
- Check service health status

**"Rolling update failed"**
- Ensure no custom container names are set
- Check service dependencies and health checks

## Migration from Older Versions

### From Manual Traefik Setup:
1. **If using auto-generated domains:** Remove all Traefik labels from docker-compose files
2. **If using custom domains:** Update Traefik labels to Coolify format (see Custom Domain Labels section)
3. **Remove custom networks** references  
4. **Add domain configuration** in Coolify UI
5. **Replace hardcoded URLs** with magic variables
6. **Test thoroughly** before going live

### From Coolify 3.x:
1. **Update docker-compose syntax** to remove deprecated features
2. **Reconfigure domains** in new UI (format may have changed)
3. **Update environment variables** to use new magic variable format
4. **Enable new features** like rolling updates

## Best Practices Summary

### File Organization:
```
your-project/
├── docker-compose.yml          # Clean, Coolify 4.0 compliant
├── .env.example               # Template for required variables
├── backend/
│   └── Dockerfile
├── frontend/  
│   └── Dockerfile
└── DEPLOYMENT.md              # Project-specific deployment notes
```

### Environment Management:
- **Never commit secrets** to git
- **Use .env.example** to document required variables
- **Set variables in Coolify UI** not in compose files
- **Use magic variables** for service discovery

### Monitoring & Maintenance:
- **Monitor container health** through Coolify dashboard
- **Check logs regularly** for any issues
- **Update base images** periodically for security
- **Test deployments** in staging environment first

---

## Quick Reference Commands

```bash
# Check all containers
docker ps -a

# View container logs
docker logs <container-name> --tail 50 -f

# Check Traefik proxy logs  
docker logs coolify-proxy --tail 20

# Test internal service connectivity
docker exec <container> curl http://localhost:<port>/health

# Check network connectivity
docker network ls
docker network inspect coolify

# Emergency: Restart all services
docker-compose down && docker-compose up -d
```

---

*Last Updated: August 2025*  
*Based on Coolify v4.0.0-beta.421+*