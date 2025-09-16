#!/bin/bash

# CI/CD Setup Script for RoyalPrompts
# This script helps you set up the necessary components for CI/CD

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_status "🚀 Setting up CI/CD for RoyalPrompts Backend..."

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Get droplet information
print_status "📝 Please provide your DigitalOcean droplet information:"
read -p "Droplet IP address: " DROPLET_IP
read -p "Droplet username (default: root): " DROPLET_USER
DROPLET_USER=${DROPLET_USER:-root}
read -p "SSH port (default: 22): " SSH_PORT
SSH_PORT=${SSH_PORT:-22}

# Generate SSH key for CI/CD
print_status "🔑 Generating SSH key for CI/CD deployment..."
SSH_KEY_PATH="$HOME/.ssh/royalprompts_cicd"
ssh-keygen -t rsa -b 4096 -C "github-actions@royalprompts.com" -f "$SSH_KEY_PATH" -N ""

print_success "✅ SSH key generated at $SSH_KEY_PATH"

# Copy public key to droplet
print_status "📤 Copying SSH public key to droplet..."
ssh-copy-id -i "$SSH_KEY_PATH.pub" "$DROPLET_USER@$DROPLET_IP"

print_success "✅ SSH key copied to droplet"

# Test SSH connection
print_status "🔍 Testing SSH connection..."
if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 "$DROPLET_USER@$DROPLET_IP" "echo 'SSH connection successful'"; then
    print_success "✅ SSH connection test passed"
else
    print_error "❌ SSH connection test failed"
    exit 1
fi

# Display GitHub secrets setup instructions
print_status "📋 GitHub Repository Secrets Setup"
echo ""
echo "Go to your GitHub repository → Settings → Secrets and variables → Actions"
echo "Add these secrets:"
echo ""
echo "DROPLET_HOST=$DROPLET_IP"
echo "DROPLET_USERNAME=$DROPLET_USER"
echo "DROPLET_PORT=$SSH_PORT"
echo "DROPLET_SSH_KEY=$(cat $SSH_KEY_PATH)"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "📝 Creating .env file from template..."
    cp env.production.example .env
    print_warning "⚠️ Please edit .env file with your actual configuration:"
    print_warning "  - MONGODB_URL (your MongoDB Atlas connection string)"
    print_warning "  - SECRET_KEY (generate a secure random key)"
    print_warning "  - FRONTEND_URL (your domain)"
    print_warning "  - NEXT_PUBLIC_API_URL (your domain/api)"
else
    print_success "✅ .env file already exists"
fi

# Check if project is in a Git repository
if [ ! -d ".git" ]; then
    print_warning "⚠️ This directory is not a Git repository"
    print_status "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit"
    print_warning "⚠️ Please push this to a GitHub repository to use CI/CD"
else
    print_success "✅ Git repository detected"
fi

# Display next steps
print_status "🎯 Next Steps:"
echo ""
echo "1. 📝 Add the GitHub secrets listed above"
echo "2. 🔧 Update .env file with your configuration"
echo "3. 📤 Push your code to GitHub repository"
echo "4. 🚀 Push to 'main' branch to trigger deployment"
echo ""
echo "📊 Your CI/CD will:"
echo "  ✅ Run tests and security scans"
echo "  ✅ Build and push Docker image"
echo "  ✅ Deploy to your DigitalOcean droplet"
echo "  ✅ Run health checks and rollback if needed"
echo ""

print_success "🎉 CI/CD setup completed!"
print_status "Your SSH key is saved at: $SSH_KEY_PATH"
print_warning "Keep this key secure and never commit it to your repository!"

