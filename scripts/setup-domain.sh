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
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name royalprompts.online www.royalprompts.online;
    return 301 https://$server_name$request_uri;
}

# HTTPS server for main domain (landing page)
server {
    listen 443 ssl;
    http2 on;
    server_name royalprompts.online www.royalprompts.online;

    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/royalprompts.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/royalprompts.online/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Landing page - Default routes (port 4321)
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

    # Health check endpoint for landing page
    location /health {
        proxy_pass http://localhost:4321/health;
        proxy_set_header Host $host;
    }
}

# HTTP server for admin panel (port 3443) - redirect to HTTPS
server {
    listen 3443;
    server_name royalprompts.online www.royalprompts.online;
    return 301 https://royalprompts.online:3443$request_uri;
}

# HTTPS server for admin panel (port 3443)
server {
    listen 3443 ssl;
    http2 on;
    server_name royalprompts.online www.royalprompts.online;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/royalprompts.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/royalprompts.online/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle WebSocket connections for admin panel
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTP server for backend API (port 8443) - redirect to HTTPS
server {
    listen 8443;
    server_name royalprompts.online www.royalprompts.online;
    return 301 https://royalprompts.online:8443$request_uri;
}

# HTTPS server for backend API (port 8443)
server {
    listen 8443 ssl;
    http2 on;
    server_name royalprompts.online www.royalprompts.online;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/royalprompts.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/royalprompts.online/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle CORS for API - Allow admin panel origin
        add_header Access-Control-Allow-Origin "https://royalprompts.online:3443" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header Access-Control-Allow-Credentials "true" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://royalprompts.online:3443" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header Access-Control-Allow-Credentials "true" always;
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
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
    echo "Your services should now be accessible at:"
    echo "  🌐 https://royalprompts.online (Landing Page - HTTPS)"
    echo "  🔧 https://royalprompts.online:3443 (Admin Panel - HTTPS)"
    echo "  📡 https://royalprompts.online:8443 (Backend API - HTTPS)"
    echo ""
    echo "Note: Make sure SSL certificates are installed with:"
    echo "  sudo certbot --nginx -d royalprompts.online -d www.royalprompts.online"
    echo ""
    echo "Make sure all containers are running:"
    echo "  docker ps | grep royalprompts"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi
