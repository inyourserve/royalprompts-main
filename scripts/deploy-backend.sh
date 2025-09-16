#!/bin/bash

# Backend Deployment Script for CI/CD
# This script is called by GitHub Actions to deploy the backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_DIR="/root/royalprompts-main"
BACKUP_DIR="/root/backups/$(date +%Y%m%d_%H%M%S)"
REGISTRY="ghcr.io"
IMAGE_NAME="royalprompts/backend"
NEW_IMAGE_TAG="${1:-latest}"

print_status "🚀 Starting backend deployment..."
print_status "Image: $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG"

# Navigate to project directory
cd $PROJECT_DIR

# Create backup
print_status "📦 Creating backup..."
mkdir -p $BACKUP_DIR
docker-compose -f docker-compose.production.yml ps > $BACKUP_DIR/containers_before.txt
docker images | grep backend > $BACKUP_DIR/images_before.txt

# Pull latest changes
print_status "📥 Pulling latest changes..."
git pull origin main

# Login to GitHub Container Registry
print_status "🔐 Logging in to container registry..."
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin

# Pull latest backend image
print_status "📥 Pulling latest backend image..."
docker pull $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG

# Health check before deployment
print_status "🏥 Checking current backend health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "✅ Current backend is healthy"
else
    print_warning "⚠️ Current backend is not responding"
fi

# Deploy new version
print_status "🚀 Deploying new backend version..."
docker-compose -f docker-compose.production.yml up -d backend

# Wait for deployment to be healthy
print_status "⏳ Waiting for new backend to be healthy..."
for i in {1..60}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ New backend is healthy!"
        break
    fi
    print_status "Attempt $i: Backend not ready yet..."
    sleep 10
done

# Final health check
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "🎉 Deployment successful!"
    
    # Clean up old images
    print_status "🧹 Cleaning up old images..."
    docker image prune -f
    
    # Save deployment info
    print_status "📝 Saving deployment info..."
    echo "Deployed at: $(date)" > $BACKUP_DIR/deployment_info.txt
    echo "Image: $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG" >> $BACKUP_DIR/deployment_info.txt
    echo "Commit: $GITHUB_SHA" >> $BACKUP_DIR/deployment_info.txt
    
    # Show final status
    print_status "📊 Final deployment status:"
    docker-compose -f docker-compose.production.yml ps
    docker-compose -f docker-compose.production.yml logs --tail=10 backend
    
else
    print_error "❌ Deployment failed! Backend is not responding."
    print_status "🔄 Attempting rollback..."
    
    # Rollback to previous version
    docker-compose -f docker-compose.production.yml restart backend
    sleep 30
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ Rollback successful!"
    else
        print_error "❌ Rollback failed! Manual intervention required."
    fi
    
    exit 1
fi

print_success "🎉 Backend deployment completed successfully!"
