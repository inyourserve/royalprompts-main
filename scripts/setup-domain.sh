#!/bin/bash

# Setup domain configuration for royalprompts.online
# This script configures Nginx to proxy the domain to port 4321

set -e

echo "🌐 Setting up domain configuration for royalprompts.online..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    apt update
    apt install -y nginx
fi

# Create the domain configuration
echo "📝 Creating Nginx configuration for royalprompts.online..."
cat > /etc/nginx/sites-available/royalprompts.online << 'EOF'
server {
    listen 80;
    server_name royalprompts.online www.royalprompts.online;

    # For now, let's keep it simple with HTTP
    location / {
        proxy_pass http://localhost:4321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle WebSocket connections (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:4321/health;
        proxy_set_header Host $host;
    }
}
EOF

# Enable the site
echo "🔗 Enabling the site configuration..."
ln -sf /etc/nginx/sites-available/royalprompts.online /etc/nginx/sites-enabled/

# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "🗑️ Removing default Nginx site..."
    rm /etc/nginx/sites-enabled/default
fi

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    systemctl reload nginx
    
    # Enable Nginx to start on boot
    systemctl enable nginx
    
    echo "🎉 Domain setup complete!"
    echo ""
    echo "Your landing page should now be accessible at:"
    echo "  🌐 http://royalprompts.online"
    echo "  🌐 http://www.royalprompts.online"
    echo ""
    echo "Make sure your landing page container is running on port 4321:"
    echo "  docker ps | grep royalprompts_landing"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi
