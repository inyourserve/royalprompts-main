#!/bin/bash

# CI/CD Setup Script for RoyalPrompts (Using Existing SSH Key)
# This script helps you set up CI/CD with your existing SSH key

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

print_status "🚀 Setting up CI/CD for RoyalPrompts Backend (Using Existing SSH Key)..."

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

# Test SSH connection with existing key
print_status "🔍 Testing SSH connection with your existing key..."
if ssh -o ConnectTimeout=10 "$DROPLET_USER@$DROPLET_IP" "echo 'SSH connection successful'"; then
    print_success "✅ SSH connection test passed with your existing key"
else
    print_error "❌ SSH connection test failed"
    print_warning "Make sure your SSH key is loaded in ssh-agent or try:"
    print_warning "ssh-add ~/.ssh/id_ed25519"
    exit 1
fi

# Get the private key content
print_status "🔑 Getting your private SSH key content..."
PRIVATE_KEY_PATH=""
if [ -f "$HOME/.ssh/id_ed25519" ]; then
    PRIVATE_KEY_PATH="$HOME/.ssh/id_ed25519"
elif [ -f "$HOME/.ssh/id_rsa" ]; then
    PRIVATE_KEY_PATH="$HOME/.ssh/id_rsa"
else
    print_error "❌ Could not find SSH private key in ~/.ssh/"
    print_warning "Please provide the path to your private key:"
    read -p "Private key path: " PRIVATE_KEY_PATH
fi

if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    print_error "❌ Private key file not found: $PRIVATE_KEY_PATH"
    exit 1
fi

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

# Display GitHub secrets setup instructions
print_status "📋 GitHub Repository Secrets Setup"
echo ""
echo "Go to your GitHub repository → Settings → Secrets and variables → Actions"
echo "Add these secrets:"
echo ""
echo "DROPLET_HOST=$DROPLET_IP"
echo "DROPLET_USERNAME=$DROPLET_USER"
echo "DROPLET_PORT=$SSH_PORT"
echo ""
echo "For DROPLET_SSH_KEY, copy the content of your private key:"
echo "cat $PRIVATE_KEY_PATH"
echo ""
print_warning "⚠️ Copy the ENTIRE private key content (including -----BEGIN and -----END lines)"
echo ""

# Test if we can read the private key
print_status "🔍 Testing private key access..."
if head -1 "$PRIVATE_KEY_PATH" | grep -q "BEGIN.*PRIVATE KEY"; then
    print_success "✅ Private key format looks correct"
    print_status "📋 Your private key content:"
    echo "----------------------------------------"
    cat "$PRIVATE_KEY_PATH"
    echo "----------------------------------------"
else
    print_error "❌ Private key format doesn't look correct"
    exit 1
fi

# Display next steps
print_status "🎯 Next Steps:"
echo ""
echo "1. 📝 Add the GitHub secrets listed above"
echo "2. 🔧 Update .env file with your configuration:"
echo "   - MONGODB_URL (your MongoDB Atlas connection string)"
echo "   - SECRET_KEY (generate a secure random key)"
echo "   - FRONTEND_URL (your domain)"
echo "   - NEXT_PUBLIC_API_URL (your domain/api)"
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
print_status "Your existing SSH key will be used for deployment"
print_warning "Keep your private key secure and never commit it to your repository!"
