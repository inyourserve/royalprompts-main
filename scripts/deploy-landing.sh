#!/bin/bash

# Landing Page Deployment Script for CI/CD
# This script is called by GitHub Actions to deploy the landing page

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
LANDING_DIR="$PROJECT_DIR/landing"
BACKUP_DIR="/root/backups/landing_$(date +%Y%m%d_%H%M%S)"
REGISTRY="ghcr.io"
IMAGE_NAME="royalprompts/landing"
NEW_IMAGE_TAG="${1:-latest}"
CONTAINER_NAME="royalprompts_landing"
PORT="8080"

print_status "🚀 Starting landing page deployment..."
print_status "Image: $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG"
print_status "Port: $PORT"

# Navigate to project directory
cd $PROJECT_DIR

# Create backup
print_status "📦 Creating backup..."
mkdir -p $BACKUP_DIR
docker-compose -f docker-compose.landing.yml ps > $BACKUP_DIR/containers_before.txt 2>/dev/null || true
docker images | grep landing > $BACKUP_DIR/images_before.txt 2>/dev/null || true

# Pull latest changes
print_status "📥 Pulling latest changes..."
git pull origin main

# Login to GitHub Container Registry
print_status "🔐 Logging in to container registry..."
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin

# Pull latest landing image
print_status "📥 Pulling latest landing image..."
docker pull $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG

# Health check before deployment
print_status "🏥 Checking current landing page health..."
if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
    print_success "✅ Current landing page is healthy"
else
    print_warning "⚠️ Current landing page is not responding"
fi

# Deploy new version
print_status "🚀 Deploying new landing page version..."
docker-compose -f docker-compose.landing.yml down
docker-compose -f docker-compose.landing.yml up -d

# Wait for deployment to be healthy
print_status "⏳ Waiting for new landing page to be healthy..."
for i in {1..60}; do
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "✅ New landing page is healthy!"
        break
    fi
    print_status "Attempt $i: Landing page not ready yet..."
    sleep 10
done

# Final health check
if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
    print_success "🎉 Landing page deployment successful!"
    
    # Clean up old images
    print_status "🧹 Cleaning up old images..."
    docker image prune -f
    
    # Save deployment info
    print_status "📝 Saving deployment info..."
    echo "Deployed at: $(date)" > $BACKUP_DIR/deployment_info.txt
    echo "Image: $REGISTRY/$IMAGE_NAME:$NEW_IMAGE_TAG" >> $BACKUP_DIR/deployment_info.txt
    echo "Commit: $GITHUB_SHA" >> $BACKUP_DIR/deployment_info.txt
    echo "Port: $PORT" >> $BACKUP_DIR/deployment_info.txt
    
    # Show final status
    print_status "📊 Final deployment status:"
    docker-compose -f docker-compose.landing.yml ps
    docker-compose -f docker-compose.landing.yml logs --tail=10 landing
    
    print_success "🌐 Landing page: http://localhost:$PORT"
    print_success "🏥 Health check: http://localhost:$PORT/health"
    
else
    print_error "❌ Landing page deployment failed! Landing page is not responding."
    print_status "🔄 Attempting rollback..."
    
    # Rollback to previous version
    docker-compose -f docker-compose.landing.yml restart
    sleep 30
    
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "✅ Rollback successful!"
    else
        print_error "❌ Rollback failed! Manual intervention required."
    fi
    
    exit 1
fi

print_success "🎉 Landing page deployment completed successfully!"
