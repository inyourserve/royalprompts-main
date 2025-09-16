# Deployment & CI/CD

Workerlly uses GitHub Actions for deployment to Digital Ocean droplets. Pretty standard Docker-based setup with two environments.

## Infrastructure Setup

```
GitHub Repository
├── main branch     → Production (username/workerlly:latest)
├── test branch     → Test (username/workerlly:test)
└── Other branches  → No deployment

Production:
├── Digital Ocean Droplet
├── Container: workerlly
├── Port: 8000
└── Image: username/workerlly:latest

Test:
├── Digital Ocean Droplet  
├── Container: workerlly-test
├── Port: 8001
└── Image: username/workerlly:test
```

## GitHub Actions Workflow

File: `.github/workflows/deploy.yml`

### Triggers

```yaml
on:
  push:
    branches:
      - main    # Production deployment
      - test    # Test deployment
```

### Build Job

Handles linting, building, and pushing Docker images:

```yaml
build:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --ignore=E501,F401,W503,E722,F841,E302,F811,E131

    - name: Build Docker image
      run: |
        if [[ $GITHUB_REF == 'refs/heads/main' ]]; then
          docker build -t username/workerlly:latest .
        else
          docker build -t username/workerlly:test .
        fi

    - name: Log in to DockerHub
      run: echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin

    - name: Push Docker image
      run: |
        if [[ $GITHUB_REF == 'refs/heads/main' ]]; then
          docker push username/workerlly:latest
        else
          docker push username/workerlly:test
        fi
```

### Production Deployment

Runs only on main branch:

```yaml
deploy-prod:
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest
  needs: build
  steps:
    - name: Set up SSH
      uses: webfactory/ssh-agent@v0.5.3
      with:
        ssh-private-key: ${{ secrets.DO_DROPLET_SSH_KEY }}

    - name: Deploy to Production Server
      run: |
        ssh -o StrictHostKeyChecking=no root@${{ secrets.DO_DROPLET_IP }} << EOF
          docker pull username/workerlly:latest
          docker stop workerlly || true
          docker rm workerlly || true
          docker run -d --name workerlly \
            -p 8000:8000 \
            -e SECRET_KEY='${{ secrets.SECRET_KEY }}' \
            -e AWS_ACCESS_KEY='${{ secrets.AWS_ACCESS_KEY }}' \
            -e AWS_SECRET_ACCESS_KEY='${{ secrets.AWS_SECRET_ACCESS_KEY }}' \
            -e S3_BUCKET_NAME='${{ secrets.S3_BUCKET_NAME }}' \
            -e REDIS_HOST='${{ secrets.REDIS_HOST }}' \
            -e REDIS_PORT='${{ secrets.REDIS_PORT }}' \
            -e REDIS_PASSWORD='${{ secrets.REDIS_PASSWORD }}' \
            -e FIREBASE_CREDENTIALS_JSON='${{ secrets.FIREBASE_SERVICE_ACCOUNT }}' \
            -e FIREBASE_PROJECT_ID='${{ secrets.FIREBASE_PROJECT_ID }}' \
            username/workerlly:latest
        EOF
```

### Test Deployment

Same process but for test branch on port 8001:

```yaml
deploy-test:
  if: github.ref == 'refs/heads/test'
  runs-on: ubuntu-latest
  needs: build
  steps:
    - name: Deploy to Test Server
      run: |
        ssh -o StrictHostKeyChecking=no root@${{ secrets.DO_TEST_DROPLET_IP }} << EOF
          docker pull username/workerlly:test
          docker stop workerlly-test || true
          docker rm workerlly-test || true
          docker run -d --name workerlly-test \
            -p 8001:8000 \
            [same env vars as production]
            username/workerlly:test
        EOF
```

## Dockerfile

Python 3.10-slim with WeasyPrint dependencies for PDF generation:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

# Install system deps for WeasyPrint (PDF generation)
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Required Secrets

Set these in GitHub repository settings:

```bash
# DockerHub
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token

# Production Server
DO_DROPLET_IP=your_production_server_ip
DO_DROPLET_SSH_KEY=your_ssh_private_key

# Test Server  
DO_TEST_DROPLET_IP=your_test_server_ip
DO_TEST_DROPLET_SSH_KEY=your_test_ssh_private_key

# App Environment Variables
SECRET_KEY=your_jwt_secret
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your_s3_bucket
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}
FIREBASE_PROJECT_ID=workerlly-notifications
```

## Manual Deployment

If you need to deploy manually:

### Build & Push

```bash
# Build image
docker build -t username/workerlly:latest .

# Push to DockerHub
docker login
docker push username/workerlly:latest
```

### Deploy on Server

```bash
# SSH into server
ssh root@your_server_ip

# Pull and run
docker pull username/workerlly:latest
docker stop workerlly || true
docker rm workerlly || true

docker run -d --name workerlly \
  -p 8000:8000 \
  -e SECRET_KEY='your_secret' \
  -e AWS_ACCESS_KEY='your_aws_key' \
  -e AWS_SECRET_ACCESS_KEY='your_aws_secret' \
  -e S3_BUCKET_NAME='your_bucket' \
  -e REDIS_HOST='your_redis_host' \
  -e REDIS_PASSWORD='your_redis_password' \
  -e FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}' \
  username/workerlly:latest
```

## Troubleshooting

### Common Issues

**Build fails on Docker Hub push:**
- Check DOCKERHUB_TOKEN is valid
- Make sure username is correct

**SSH connection fails:**
- Verify SSH key is correct
- Check server IP address
- Ensure server allows SSH access

**Container won't start:**
- Check environment variables are set
- Look at container logs: `docker logs workerlly`
- Verify all secrets are configured

**App not accessible:**
- Check if port 8000 is open on server
- Verify container is running: `docker ps`
- Check app logs for errors

### Useful Commands

```bash
# Check running containers
docker ps

# View logs
docker logs workerlly

# Shell into container
docker exec -it workerlly bash

# Restart container
docker restart workerlly

# Clean up old images
docker system prune -f
```

## Security Best Practices

- SSH keys are stored as GitHub secrets
- Environment variables passed securely
- Docker images use non-root user (could be improved)
- HTTPS should be configured with reverse proxy
- Database credentials are hardcoded (not ideal)

## Improvements Needed

- Add health checks to Dockerfile
- Set up proper logging (currently just console)
- Use docker-compose for easier management
- Add staging environment
- Implement blue-green deployment
- Add automated tests in CI pipeline

The deployment works but it's pretty basic. Good enough for a small project but could use some improvements for production scale.
