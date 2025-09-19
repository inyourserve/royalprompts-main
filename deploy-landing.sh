#!/bin/bash

# Deploy Landing Page with CI/CD Configuration
echo "🚀 Deploying RoyalPrompts Landing Page..."

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
CONTAINER_NAME="royalprompts_landing"
IMAGE_NAME="royalprompts-landing"
PORT="4321"  # Port 4321 (Astro default, 8000=backend, 3000=admin)

print_status "🚀 Starting landing page deployment..."
print_status "Container: $CONTAINER_NAME"
print_status "Port: $PORT"
print_status "Image: $IMAGE_NAME:latest"

# Navigate to landing directory
cd $LANDING_DIR

# Build the Docker image
print_status "🔨 Building Docker image..."
docker build -t $IMAGE_NAME:latest .

if [ $? -eq 0 ]; then
    print_success "✅ Docker image built successfully!"
    
    # Stop existing container if running
    print_status "🛑 Stopping existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # Run the new container
    print_status "🚀 Starting new container..."
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        -p $PORT:80 \
        $IMAGE_NAME:latest
    
    if [ $? -eq 0 ]; then
        print_success "✅ Container started successfully!"
        
        # Wait for deployment to be healthy
        print_status "⏳ Waiting for landing page to be healthy..."
        for i in {1..30}; do
            if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
                print_success "✅ Landing page is healthy!"
                break
            fi
            print_status "Attempt $i: Landing page not ready yet..."
            sleep 5
        done
        
        # Final health check
        if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
            print_success "🎉 Landing page deployed successfully!"
            
            # Show final status
            print_status "📊 Final deployment status:"
            docker ps | grep $CONTAINER_NAME
            echo ""
            print_success "🌐 Landing page: http://localhost:$PORT"
            print_success "🏥 Health check: http://localhost:$PORT/health"
            
        else
            print_error "❌ Deployment failed! Landing page is not responding."
            exit 1
        fi
    else
        print_error "❌ Failed to start container"
        exit 1
    fi
else
    print_error "❌ Docker build failed"
    exit 1
fi

print_success "🎉 Landing page deployment completed successfully!"
