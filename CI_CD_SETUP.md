
# 🚀 CI/CD Setup Guide for RoyalPrompts Backend

This guide will help you set up automated CI/CD for your backend deployment to DigitalOcean.

## 📋 Prerequisites

- GitHub repository with your code
- DigitalOcean droplet with Docker installed
- SSH access to your droplet
- GitHub Container Registry access

## 🔧 GitHub Repository Setup

### 1. Create GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

#### Required Secrets:
```
DROPLET_HOST=your-droplet-ip-address
DROPLET_USERNAME=root
DROPLET_SSH_KEY=your-private-ssh-key
DROPLET_PORT=22
```

#### Optional Secrets (for staging):
```
STAGING_HOST=your-staging-server-ip
STAGING_USERNAME=root
STAGING_SSH_KEY=your-staging-ssh-key
STAGING_PORT=22
```

### 2. Generate SSH Key for Deployment

On your local machine:
```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "github-actions@royalprompts.com" -f ~/.ssh/royalprompts_deploy

# Copy public key to your droplet
ssh-copy-id -i ~/.ssh/royalprompts_deploy.pub root@your-droplet-ip

# Copy private key content to GitHub secret DROPLET_SSH_KEY
cat ~/.ssh/royalprompts_deploy
```

### 3. Set up GitHub Container Registry

The workflow automatically uses GitHub Container Registry (ghcr.io). No additional setup needed.

## 🏗️ Workflow Files

### Basic CI/CD (`backend-deploy.yml`)
- ✅ Code quality checks
- ✅ Docker image build and push
- ✅ Automated deployment to production
- ✅ Health checks and rollback

### Advanced CI/CD (`backend-advanced-deploy.yml`)
- ✅ Code formatting and linting
- ✅ Security scanning
- ✅ Staging and production environments
- ✅ Manual deployment triggers
- ✅ Comprehensive health checks
- ✅ Automatic rollback on failure

## 🚀 Deployment Process

### Automatic Deployment
1. **Push to `main` branch** → Deploys to production
2. **Push to `develop` branch** → Deploys to staging (if configured)
3. **Pull Request** → Runs tests only

### Manual Deployment
1. Go to Actions tab in GitHub
2. Select "Advanced Backend CI/CD Pipeline"
3. Click "Run workflow"
4. Choose environment (production/staging)
5. Click "Run workflow"

## 📊 Workflow Steps

### 1. Quality Checks
- Python syntax validation
- Code formatting (Black)
- Linting (Flake8)
- Basic import tests

### 2. Security Scan
- Bandit security analysis
- Safety vulnerability check

### 3. Build and Push
- Docker image build
- Push to GitHub Container Registry
- Multi-architecture support

### 4. Deploy
- SSH to DigitalOcean droplet
- Pull latest code
- Deploy new Docker image
- Health checks
- Automatic rollback on failure

## 🔍 Monitoring and Logs

### View Deployment Logs
1. Go to GitHub Actions tab
2. Click on the latest workflow run
3. Expand each job to see detailed logs

### Monitor on Server
```bash
# SSH to your droplet
ssh root@your-droplet-ip

# Check container status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f backend

# Check health
curl http://localhost:8000/health
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Test SSH connection
ssh -i ~/.ssh/royalprompts_deploy root@your-droplet-ip

# Check SSH key in GitHub secrets
# Ensure private key is copied correctly (including headers)
```

#### 2. Docker Login Failed
```bash
# Check GitHub token permissions
# Ensure repository has Container Registry access
```

#### 3. Health Check Failed
```bash
# Check backend logs
docker-compose -f docker-compose.production.yml logs backend

# Check if MongoDB Atlas is accessible
# Verify environment variables in .env file
```

#### 4. Rollback Issues
```bash
# Manual rollback
docker-compose -f docker-compose.production.yml restart backend

# Check previous image
docker images | grep backend
```

## 🔒 Security Best Practices

### 1. SSH Key Security
- Use dedicated SSH key for CI/CD
- Rotate keys regularly
- Never commit private keys to repository

### 2. Environment Variables
- Store sensitive data in GitHub Secrets
- Use different secrets for staging/production
- Regularly rotate secrets

### 3. Container Security
- Use specific image tags (not `latest`)
- Regular security scans
- Keep base images updated

## 📈 Advanced Features

### 1. Staging Environment
- Separate staging server
- Automatic deployment from `develop` branch
- Staging-specific environment variables

### 2. Blue-Green Deployment
- Zero-downtime deployments
- Instant rollback capability
- Load balancer integration

### 3. Monitoring Integration
- Health check endpoints
- Log aggregation
- Performance metrics

## 🎯 Next Steps

1. **Set up staging environment** (optional)
2. **Configure monitoring** (Prometheus/Grafana)
3. **Set up log aggregation** (ELK stack)
4. **Configure alerts** (Slack/Email notifications)
5. **Set up database backups** (automated)

## 📞 Support

If you encounter issues:
1. Check GitHub Actions logs
2. Verify server connectivity
3. Check Docker container status
4. Review environment variables
5. Contact support team

---

**🎉 Congratulations!** Your backend now has automated CI/CD with:
- ✅ Automated testing and deployment
- ✅ Health checks and rollback
- ✅ Security scanning
- ✅ Multi-environment support
- ✅ Comprehensive monitoring

