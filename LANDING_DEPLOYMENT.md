# 🚀 Landing Page Deployment Guide

This guide covers the complete CI/CD setup for the RoyalPrompt landing page, inspired by the existing backend and admin frontend deployment patterns.

## 📋 Overview

The landing page deployment includes:
- ✅ **Astro-based static site** with Tailwind CSS
- ✅ **Docker containerization** with nginx
- ✅ **Automated CI/CD** with GitHub Actions
- ✅ **Health checks** and rollback capabilities
- ✅ **Multi-environment support** (staging/production)
- ✅ **Security scanning** and quality checks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Actions │───▶│  DigitalOcean   │
│                 │    │                 │    │                 │
│  landing/       │    │  Build & Test   │    │  Docker Host    │
│  - Astro App    │    │  Deploy         │    │  - nginx:80     │
│  - Tailwind CSS │    │  Health Check   │    │  - Port 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Manual Deployment

```bash
# Navigate to project root
cd /path/to/royalprompts-main

# Run deployment script
./deploy-landing.sh
```

### 2. Docker Compose Deployment

```bash
# Deploy with docker-compose
docker-compose -f docker-compose.landing.yml up -d

# Check status
docker-compose -f docker-compose.landing.yml ps
```

### 3. GitHub Actions Deployment

- **Automatic**: Push to `main` branch → Deploys to production
- **Manual**: Go to Actions tab → Run "Advanced Landing Page CI/CD"

## 📁 File Structure

```
landing/
├── Dockerfile              # Multi-stage Docker build
├── nginx.conf              # nginx configuration
├── package.json            # Node.js dependencies
├── astro.config.mjs        # Astro configuration
├── tailwind.config.mjs     # Tailwind CSS config
└── src/
    ├── layouts/
    │   └── Layout.astro    # Main layout component
    └── pages/
        ├── index.astro     # Homepage
        ├── about.astro     # About page
        ├── contact.astro   # Contact page
        ├── privacy.astro   # Privacy policy
        ├── terms.astro     # Terms of service
        └── screenshots.astro # Screenshots page

.github/workflows/
├── landing-deploy.yml           # Basic CI/CD
└── landing-advanced-deploy.yml  # Advanced CI/CD

docker-compose.landing.yml       # Standalone deployment
docker-compose.production.yml    # Full stack deployment
deploy-landing.sh                # Manual deployment script
```

## 🔧 Configuration

### Environment Variables

```bash
# Landing page port (default: 8080)
LANDING_PORT=8080

# GitHub Container Registry
REGISTRY=ghcr.io
IMAGE_NAME=royalprompts/landing
```

### Docker Configuration

The landing page uses a multi-stage Docker build:

1. **Builder Stage**: Node.js 18 Alpine
   - Installs dependencies
   - Builds Astro application
   - Generates static files

2. **Production Stage**: nginx Alpine
   - Serves static files
   - Includes security headers
   - Gzip compression
   - Health check endpoint

## 🚀 Deployment Methods

### Method 1: Manual Script Deployment

```bash
# Make script executable
chmod +x deploy-landing.sh

# Deploy
./deploy-landing.sh
```

**Features:**
- ✅ Health checks before/after deployment
- ✅ Automatic rollback on failure
- ✅ Backup creation
- ✅ Image cleanup
- ✅ Colored output and logging

### Method 2: Docker Compose

```bash
# Standalone deployment
docker-compose -f docker-compose.landing.yml up -d

# Full stack deployment (with backend/frontend)
docker-compose -f docker-compose.production.yml up -d
```

**Features:**
- ✅ Service orchestration
- ✅ Health checks
- ✅ Automatic restarts
- ✅ Network isolation

### Method 3: GitHub Actions CI/CD

#### Basic Workflow (`landing-deploy.yml`)
- ✅ Code quality checks
- ✅ Docker image build and push
- ✅ Automated deployment to production
- ✅ Health checks and rollback

#### Advanced Workflow (`landing-advanced-deploy.yml`)
- ✅ Code formatting and linting
- ✅ Security scanning
- ✅ Staging and production environments
- ✅ Manual deployment triggers
- ✅ Comprehensive health checks
- ✅ Automatic rollback on failure

## 🔐 GitHub Secrets Setup

### Required Secrets

```bash
# Production deployment
DROPLET_HOST=your-production-server-ip
DROPLET_USERNAME=root
DROPLET_SSH_KEY=your-private-ssh-key
DROPLET_PORT=22

# Staging deployment (optional)
STAGING_HOST=your-staging-server-ip
STAGING_USERNAME=root
STAGING_SSH_KEY=your-staging-ssh-key
STAGING_PORT=22
```

### Setting up SSH Keys

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "github-actions@royalprompts.com" -f ~/.ssh/landing_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/landing_deploy.pub root@your-server-ip

# Copy private key to GitHub secret
cat ~/.ssh/landing_deploy
```

## 📊 Monitoring and Health Checks

### Health Check Endpoint

```bash
# Check landing page health
curl http://localhost:8080/health

# Expected response
healthy
```

### Container Status

```bash
# Check container status
docker ps | grep royalprompts_landing

# View logs
docker logs royalprompts_landing

# Check resource usage
docker stats royalprompts_landing
```

### nginx Logs

```bash
# Access logs
docker exec royalprompts_landing tail -f /var/log/nginx/access.log

# Error logs
docker exec royalprompts_landing tail -f /var/log/nginx/error.log
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Check Node.js version
node --version  # Should be 18+

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### 2. Docker Issues

```bash
# Check Docker daemon
docker info

# Clean up Docker
docker system prune -a

# Rebuild image
docker build --no-cache -t royalprompts-landing .
```

#### 3. nginx Issues

```bash
# Test nginx configuration
docker exec royalprompts_landing nginx -t

# Reload nginx
docker exec royalprompts_landing nginx -s reload

# Check nginx status
docker exec royalprompts_landing nginx -s status
```

#### 4. Health Check Failures

```bash
# Check if container is running
docker ps | grep landing

# Check container logs
docker logs royalprompts_landing

# Test health endpoint manually
curl -v http://localhost:8080/health
```

### Rollback Procedures

#### Manual Rollback

```bash
# Stop current container
docker stop royalprompts_landing
docker rm royalprompts_landing

# Run previous image
docker run -d --name royalprompts_landing -p 8080:80 royalprompts-landing:previous-tag
```

#### Docker Compose Rollback

```bash
# Rollback to previous version
docker-compose -f docker-compose.landing.yml down
docker-compose -f docker-compose.landing.yml up -d
```

## 🔒 Security Features

### nginx Security Headers

```nginx
# Security headers included
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer-when-downgrade
Content-Security-Policy: default-src 'self' http: https: data: blob: 'unsafe-inline'
```

### Container Security

- ✅ Non-root user execution
- ✅ Minimal Alpine Linux base
- ✅ No unnecessary packages
- ✅ Read-only filesystem where possible

## 📈 Performance Optimization

### nginx Optimizations

- ✅ Gzip compression enabled
- ✅ Static asset caching (1 year)
- ✅ Browser caching headers
- ✅ Efficient MIME types

### Build Optimizations

- ✅ Multi-stage Docker build
- ✅ Node.js dependency caching
- ✅ Astro static generation
- ✅ Tailwind CSS purging

## 🌐 Domain and SSL Setup

### Custom Domain

```bash
# Update nginx configuration
# Add your domain to server_name directive

# Update DNS records
# Point your domain to server IP
```

### SSL Certificate

```bash
# Using Let's Encrypt with Certbot
certbot --nginx -d your-domain.com

# Or use Traefik for automatic SSL
# (included in docker-compose.landing.yml)
```

## 📞 Support and Maintenance

### Regular Maintenance

```bash
# Update dependencies
cd landing
npm update

# Rebuild and deploy
./deploy-landing.sh

# Clean up old images
docker image prune -f
```

### Monitoring

- ✅ Health check endpoint: `/health`
- ✅ Container health checks
- ✅ nginx access/error logs
- ✅ GitHub Actions deployment logs

### Backup Strategy

- ✅ Automated backups before deployment
- ✅ Container state snapshots
- ✅ Image versioning with git SHA
- ✅ Rollback capabilities

## 🎯 Next Steps

1. **Set up custom domain** and SSL certificate
2. **Configure monitoring** (Prometheus/Grafana)
3. **Set up log aggregation** (ELK stack)
4. **Configure alerts** (Slack/Email notifications)
5. **Set up CDN** for global performance
6. **Implement analytics** (Google Analytics)

---

**🎉 Congratulations!** Your landing page now has:

- ✅ **Automated CI/CD** with GitHub Actions
- ✅ **Docker containerization** with nginx
- ✅ **Health checks** and rollback capabilities
- ✅ **Multi-environment support**
- ✅ **Security best practices**
- ✅ **Performance optimizations**
- ✅ **Comprehensive monitoring**

The landing page is now ready for production deployment and will automatically update whenever you push changes to the `main` branch!
