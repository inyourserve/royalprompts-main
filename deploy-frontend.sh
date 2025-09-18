#!/bin/bash

# Deploy Frontend with Live Backend Configuration
echo "🚀 Deploying RoyalPrompts Frontend with Live Backend Configuration..."

# Set environment variables for production
export NEXT_PUBLIC_API_URL=http://134.209.147.231:8000

echo "✅ Environment variables set:"
echo "   - NEXT_PUBLIC_API_URL=http://134.209.147.231:8000"
echo ""

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t royalprompts-frontend:latest ./admin

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Stop existing container if running
    echo "🛑 Stopping existing container..."
    docker stop royalprompts_frontend 2>/dev/null || true
    docker rm royalprompts_frontend 2>/dev/null || true
    
    # Run the new container
    echo "🚀 Starting new container..."
    docker run -d \
        --name royalprompts_frontend \
        --restart unless-stopped \
        -p 3000:3000 \
        -e NEXT_PUBLIC_API_URL=http://134.209.147.231:8000 \
        royalprompts-frontend:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend deployed successfully!"
        echo "🌐 Frontend: http://134.209.147.231:3000"
        echo "🔗 Backend: http://134.209.147.231:8000"
        echo ""
        echo "📋 Container status:"
        docker ps | grep royalprompts_frontend
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Docker build failed"
    exit 1
fi
