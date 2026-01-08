# OpenManus Web UI Deployment Guide

This guide provides comprehensive instructions for deploying OpenManus Web UI to various cloud platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Testing](#local-testing)
- [Deployment Platforms](#deployment-platforms)
  - [Railway](#railway)
  - [Render](#render)
  - [Fly.io](#flyio)
  - [DigitalOcean](#digitalocean)
  - [Docker Compose (Self-Hosted)](#docker-compose-self-hosted)
- [Environment Variables](#environment-variables)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **API Keys**: At least one LLM provider API key (Anthropic, OpenAI, or OpenRouter)
2. **Git**: Repository access
3. **Docker** (for local testing): [Install Docker](https://docs.docker.com/get-docker/)
4. **Platform Account**: Account on your chosen deployment platform

---

## Local Testing

Test your deployment locally before pushing to production:

### Step 1: Create Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

### Step 2: Create Config File

```bash
# Copy and configure the TOML config
cp config/config.example.toml config/config.toml

# Edit config.toml with your settings
nano config/config.toml
```

### Step 3: Build and Run with Docker Compose

```bash
# Build the image
docker-compose build

# Run the service
docker-compose up

# Or run in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f openmanus-web
```

### Step 4: Test the Application

```bash
# Health check
curl http://localhost:8000/health

# Or open in browser
open http://localhost:8000
```

### Step 5: Stop the Service

```bash
docker-compose down
```

---

## Deployment Platforms

### Railway

Railway offers the simplest deployment with automatic builds and managed infrastructure.

#### Steps

1. **Install Railway CLI** (Optional)

   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Deploy via Dashboard** (Recommended)
   - Go to [Railway Dashboard](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will detect and use `Dockerfile.web`

3. **Configure Environment Variables**
   - In Railway Dashboard, go to your project
   - Navigate to "Variables" tab
   - Add the following required variables:

     ```
     LLM_API_KEY=your-api-key-here
     ANTHROPIC_API_KEY=your-anthropic-key
     ```

4. **Optional: Deploy via CLI**

   ```bash
   railway login
   railway init
   railway up
   ```

5. **Get Your Deployment URL**
   - Go to "Settings" tab
   - Click "Generate Domain" under "Domains"
   - Your app will be available at: `https://your-app.up.railway.app`

#### Cost

- Free tier: $5 credit/month
- Pro plan: $20/month + usage

---

### Render

Render provides a Heroku-like experience with Docker support.

#### Steps

1. **Create Account**
   - Sign up at [Render](https://render.com/)
   - Connect your GitHub account

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Select your repository
   - Configure:
     - **Name**: openmanus
     - **Environment**: Docker
     - **Dockerfile Path**: `./Dockerfile.web`
     - **Instance Type**: Starter ($7/month) or Free

3. **Configure Environment Variables**
   - Scroll to "Environment Variables"
   - Click "Add Environment Variable"
   - Add required variables:

     ```
     LLM_API_KEY=your-key
     ANTHROPIC_API_KEY=your-key
     OPENAI_API_KEY=your-key (optional)
     ```

4. **Add Disk for Persistence** (Optional)
   - In "Advanced" section, add a disk:
     - **Name**: workspace-data
     - **Mount Path**: /app/workspace
     - **Size**: 1 GB

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

6. **Get Your URL**
   - Your app will be available at: `https://openmanus.onrender.com`

#### Blueprint Deployment (Alternative)

```bash
# Using render.yaml
render blueprint launch
```

#### Cost

- Free tier: Limited hours/month
- Starter: $7/month
- Standard: $25/month

---

### Fly.io

Fly.io offers global distribution and excellent Docker support.

#### Steps

1. **Install Fly CLI**

   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login**

   ```bash
   fly auth login
   ```

3. **Launch Application**

   ```bash
   # This will use fly.toml configuration
   fly launch --no-deploy

   # Or create from scratch
   fly launch --name openmanus --region sea
   ```

4. **Set Secrets** (Don't use plain env vars for sensitive data)

   ```bash
   fly secrets set LLM_API_KEY="your-api-key-here"
   fly secrets set ANTHROPIC_API_KEY="your-anthropic-key"
   fly secrets set OPENAI_API_KEY="your-openai-key"
   ```

5. **Create Volume for Persistence**

   ```bash
   fly volumes create workspace_data --region sea --size 1
   ```

6. **Deploy**

   ```bash
   fly deploy
   ```

7. **Open Your App**

   ```bash
   fly open
   # Or get URL
   fly info
   ```

8. **Monitor Logs**

   ```bash
   fly logs
   ```

#### Useful Commands

```bash
# Scale the app
fly scale count 1

# Check status
fly status

# SSH into instance
fly ssh console

# Scale VM resources
fly scale vm shared-cpu-1x --memory 2048
```

#### Cost

- Free tier: Generous allowance
- Pay as you go: ~$5-10/month for basic usage

---

### DigitalOcean

Deploy on DigitalOcean using App Platform or Droplets.

#### Option A: App Platform (Recommended)

1. **Create Account**
   - Sign up at [DigitalOcean](https://www.digitalocean.com/)

2. **Deploy via App Platform**
   - Go to "Create" → "Apps"
   - Connect GitHub repository
   - Configure:
     - **Source**: GitHub repo
     - **Branch**: main
     - **Type**: Docker
     - **Dockerfile**: Dockerfile.web

3. **Set Environment Variables**

   ```
   LLM_API_KEY=your-key
   ANTHROPIC_API_KEY=your-key
   HOST=0.0.0.0
   PORT=8000
   ```

4. **Deploy**
   - Click "Next" through the wizard
   - Choose your plan ($5-12/month)
   - Click "Create Resources"

#### Option B: Droplet (Docker)

1. **Create Droplet**

   ```bash
   # Create a Docker droplet via dashboard or CLI
   doctl compute droplet create openmanus \
     --image docker-20-04 \
     --size s-1vcpu-1gb \
     --region nyc1
   ```

2. **SSH into Droplet**

   ```bash
   ssh root@your-droplet-ip
   ```

3. **Clone and Deploy**

   ```bash
   # Install Docker Compose
   apt-get update
   apt-get install docker-compose -y

   # Clone repository
   git clone https://github.com/yourusername/openmanus.git
   cd openmanus

   # Create .env file
   nano .env
   # Add your environment variables

   # Deploy
   docker-compose up -d
   ```

4. **Setup Nginx (Optional)**

   ```bash
   apt-get install nginx certbot python3-certbot-nginx -y

   # Configure nginx
   nano /etc/nginx/sites-available/openmanus
   ```

   Add:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   Enable:

   ```bash
   ln -s /etc/nginx/sites-available/openmanus /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx

   # Get SSL certificate
   certbot --nginx -d your-domain.com
   ```

#### Cost

- App Platform: $5-12/month
- Droplet: $6/month (1GB RAM)

---

### Docker Compose (Self-Hosted)

Deploy on any VPS or server with Docker.

#### Prerequisites

- Ubuntu 20.04+ or similar Linux distro
- Docker and Docker Compose installed
- Domain name (optional but recommended)

#### Steps

1. **Install Docker** (if not installed)

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh

   # Install Docker Compose
   apt-get install docker-compose -y
   ```

2. **Clone Repository**

   ```bash
   git clone https://github.com/yourusername/openmanus.git
   cd openmanus
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

4. **Deploy**

   ```bash
   docker-compose up -d
   ```

5. **Check Status**

   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

6. **Setup Reverse Proxy** (Recommended)
   - Use Nginx or Caddy for HTTPS
   - See DigitalOcean Droplet section for Nginx example

   Or use Caddy (easier):

   ```bash
   # Install Caddy
   apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | tee /etc/apt/sources.list.d/caddy-stable.list
   apt update
   apt install caddy

   # Configure Caddyfile
   nano /etc/caddy/Caddyfile
   ```

   Add:

   ```
   your-domain.com {
       reverse_proxy localhost:8000
   }
   ```

   ```bash
   systemctl restart caddy
   ```

#### Updates

```bash
cd openmanus
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | Your LLM provider API key | `sk-ant-...` |
| `LLM_MODEL` | Model to use | `claude-3-7-sonnet-20250219` |
| `LLM_BASE_URL` | API endpoint | `https://api.anthropic.com/v1/` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `BROWSER_HEADLESS` | Run browser headless | `true` |
| `SEARCH_ENGINE` | Search engine | `Google` |
| `DAYTONA_API_KEY` | Daytona sandbox API key | - |

### LLM Provider Examples

**Anthropic (Claude)**:

```bash
LLM_MODEL=claude-3-7-sonnet-20250219
LLM_BASE_URL=https://api.anthropic.com/v1/
LLM_API_KEY=sk-ant-xxxxx
```

**OpenAI**:

```bash
LLM_MODEL=gpt-4-turbo
LLM_BASE_URL=https://api.openai.com/v1/
LLM_API_KEY=sk-xxxxx
```

**OpenRouter** (Multiple models):

```bash
LLM_MODEL=anthropic/claude-3-sonnet
LLM_BASE_URL=https://openrouter.ai/api/v1/
LLM_API_KEY=sk-or-xxxxx
```

---

## Security Best Practices

### 1. API Key Management

- ✅ **DO**: Use platform secret management (Railway Secrets, Render Environment Variables, Fly Secrets)
- ❌ **DON'T**: Commit `.env` files or hardcode API keys in code
- Use different API keys for dev/staging/production

### 2. Enable HTTPS

- All platforms provide free HTTPS
- Railway/Render/Fly: Automatic HTTPS
- Self-hosted: Use Certbot (Let's Encrypt) or Caddy

### 3. Add Basic Authentication

Create a middleware in your web app:

```python
# In web_ui.py or similar
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

app = FastAPI()
security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("BASIC_AUTH_USERNAME", "admin")
    correct_password = os.getenv("BASIC_AUTH_PASSWORD", "changeme")

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/", dependencies=[Depends(verify_credentials)])
async def root():
    return {"message": "Welcome to OpenManus"}
```

Then set environment variables:

```bash
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your-strong-password
```

### 4. Rate Limiting

Consider adding rate limiting to prevent abuse:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    # Your endpoint logic
    pass
```

### 5. CORS Configuration

If building a separate frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 7. Regular Updates

```bash
# Keep dependencies updated
pip install --upgrade -r requirements.txt

# Update base images
docker-compose pull
docker-compose up -d
```

---

## Troubleshooting

### Issue: Container Won't Start

**Check logs**:

```bash
# Docker Compose
docker-compose logs -f openmanus-web

# Railway
railway logs

# Render
# View logs in dashboard

# Fly.io
fly logs
```

**Common causes**:

- Missing required environment variables
- Port already in use
- Insufficient memory
- Invalid API keys

### Issue: API Key Errors

**Symptoms**: `401 Unauthorized` or similar

**Solutions**:

1. Verify API key is set correctly:

   ```bash
   # Check environment variable
   echo $LLM_API_KEY
   ```

2. Ensure no extra spaces or quotes in `.env`:

   ```bash
   # Correct
   LLM_API_KEY=sk-ant-xxxxx

   # Wrong
   LLM_API_KEY="sk-ant-xxxxx"  # Remove quotes
   LLM_API_KEY= sk-ant-xxxxx   # Remove space
   ```

3. Check API key has sufficient credits/quota

### Issue: Browser Tools Not Working

**Symptoms**: Browser automation fails

**Solutions**:

1. Ensure Playwright is installed:

   ```dockerfile
   # In Dockerfile.web
   RUN playwright install chromium
   RUN playwright install-deps chromium
   ```

2. Set headless mode:

   ```bash
   BROWSER_HEADLESS=true
   ```

3. Increase memory allocation (browser needs RAM):
   - Railway: Scale to at least 1GB RAM
   - Render: Use Starter plan minimum
   - Fly.io: `fly scale memory 1024`

### Issue: Timeout Errors

**Symptoms**: Requests timeout after 30s

**Solutions**:

1. Increase timeouts in platform settings:
   - Railway: Adjust in settings
   - Render: Contact support for timeout increase
   - Fly.io: Increase in `fly.toml`

2. Optimize your prompts to reduce processing time

3. Use async operations where possible

### Issue: Out of Memory

**Symptoms**: Container crashes or restarts frequently

**Solutions**:

1. Increase memory limits:

   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 4G
   ```

2. Upgrade plan on your platform
3. Reduce concurrent operations
4. Disable browser automation if not needed

### Issue: Health Check Failures

**Symptoms**: Platform shows service as unhealthy

**Solutions**:

1. Verify health endpoint exists:

   ```bash
   curl http://localhost:8000/health
   ```

2. Add health endpoint to your app:

   ```python
   @app.get("/health")
   async def health():
       return {"status": "healthy"}
   ```

3. Increase health check timeouts in platform config

### Issue: Slow Performance

**Solutions**:

1. Use a more powerful instance type
2. Enable caching for repeated requests
3. Use CDN for static assets
4. Optimize database queries (if applicable)
5. Consider using Redis for session storage

### Issue: CORS Errors

**Symptoms**: Frontend can't connect to API

**Solutions**:

1. Add CORS middleware (see Security section)
2. Check `CORS_ORIGINS` environment variable
3. Ensure your frontend domain is allowed

### Getting Help

If you continue to experience issues:

1. **Check logs first**: Most problems are visible in logs
2. **GitHub Issues**: <https://github.com/Yaakovyitzchak1231/openmanus/issues>
3. **Community**: Join discussions or Discord/Slack if available
4. **Platform Support**: Contact your hosting platform's support

### Useful Debugging Commands

```bash
# Check container status
docker ps -a

# Inspect container
docker inspect <container_id>

# Execute command in container
docker exec -it <container_id> bash

# Check resource usage
docker stats

# View full logs
docker logs <container_id> --tail 1000

# Test network connectivity
docker exec -it <container_id> curl http://localhost:8000/health
```

---

## Additional Resources

- OpenManus Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)

---

## Quick Reference

### Build Commands

```bash
# Build Docker image
docker build -f Dockerfile.web -t openmanus-web .

# Build with docker-compose
docker-compose build

# Build without cache
docker-compose build --no-cache
```

### Deployment Commands

```bash
# Railway
railway up

# Render
git push  # Auto-deploys on push

# Fly.io
fly deploy

# Docker Compose
docker-compose up -d
```

### Monitoring Commands

```bash
# View logs
docker-compose logs -f
railway logs
fly logs

# Check status
docker-compose ps
railway status
fly status
```

---

**Last Updated**: January 2026
**Maintained by**: OpenManus Team
