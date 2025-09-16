#!/bin/bash

# RoyalPrompts Production Deployment Script
# For DigitalOcean Single Droplet Deployment

set -e

echo "🚀 Starting RoyalPrompts Production Deployment..."

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f env.production.example ]; then
        cp env.production.example .env
        print_warning "Please edit .env file with your actual configuration before continuing."
        print_warning "Especially update:"
        print_warning "  - SECRET_KEY (generate a secure random key)"
        print_warning "  - MONGO_ROOT_PASSWORD (use a strong password)"
        print_warning "  - FRONTEND_URL (your domain)"
        print_warning "  - NEXT_PUBLIC_API_URL (your domain/api)"
        read -p "Press Enter after updating .env file..."
    else
        print_error "env.production.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p nginx/logs
mkdir -p nginx/ssl
mkdir -p backend/logs

# Set proper permissions
print_status "Setting directory permissions..."
chmod 755 nginx/logs
chmod 755 nginx/ssl
chmod 755 backend/logs

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.production.yml down || true

# Remove old images (optional - uncomment if you want to force rebuild)
# print_status "Removing old images..."
# docker-compose -f docker-compose.production.yml down --rmi all || true

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.production.yml up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check MongoDB Atlas connection (via backend health check)
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "MongoDB Atlas connection is healthy (via backend)"
else
    print_error "MongoDB Atlas connection failed (check backend logs)"
fi

# Redis not used - removed for simplicity

# Check Backend (already checked above for MongoDB)
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is healthy"
else
    print_error "Backend API is not responding"
fi

# Check Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is healthy"
else
    print_error "Frontend is not responding"
fi

# Check Nginx
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Nginx is healthy"
else
    print_error "Nginx is not responding"
fi

# Show running containers
print_status "Running containers:"
docker-compose -f docker-compose.production.yml ps

# Show logs
print_status "Recent logs:"
docker-compose -f docker-compose.production.yml logs --tail=20

print_success "Deployment completed!"
print_status "Your application should be available at:"
print_status "  - Admin Panel: http://your-domain.com"
print_status "  - API: http://your-domain.com/api"
print_status "  - Health Check: http://your-domain.com/health"

print_warning "Next steps:"
print_warning "1. Configure your domain DNS to point to this server"
print_warning "2. Set up SSL certificates (Let's Encrypt recommended)"
print_warning "3. Update firewall rules if needed"
print_warning "4. Monitor logs: docker-compose -f docker-compose.production.yml logs -f"

print_status "To view logs: docker-compose -f docker-compose.production.yml logs -f"
print_status "To stop services: docker-compose -f docker-compose.production.yml down"
print_status "To restart services: docker-compose -f docker-compose.production.yml restart"
