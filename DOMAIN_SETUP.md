# Domain Setup Guide for royalprompts.online

This guide will help you configure your domain `royalprompts.online` to serve your landing page.

## 🌐 Current Setup

- **Domain**: `royalprompts.online`
- **Server**: DigitalOcean droplet
- **Landing Page**: Port 4321 → `http://royalprompts.online`
- **Admin Panel**: Port 3000 → `http://royalprompts.online:3000`
- **Backend API**: Port 8000 → `http://royalprompts.online:8000`

## 📋 Prerequisites

1. ✅ Domain `royalprompts.online` is configured in DigitalOcean
2. ✅ DNS is pointing to your server IP (`134.209.147.231`)
3. ✅ Landing page container is running on port 4321

## 🚀 Setup Steps

### Step 1: Run the Domain Setup Script

SSH into your server and run:

```bash
# Make the script executable
chmod +x scripts/setup-domain.sh

# Run the setup script (requires sudo)
sudo ./scripts/setup-domain.sh
```

This script will:
- Install Nginx (if not already installed)
- Create the domain configuration
- Enable the site
- Test and reload Nginx

### Step 2: Verify the Setup

Check that everything is working:

```bash
# Check if Nginx is running
sudo systemctl status nginx

# Check if your landing page container is running
docker ps | grep royalprompts_landing

# Test the domain
curl -I http://royalprompts.online
```

### Step 3: Test the Domain

Visit these URLs in your browser:
- 🌐 `http://royalprompts.online`
- 🌐 `http://www.royalprompts.online`

## 🔧 Manual Configuration (Alternative)

If you prefer to set up manually:

### 1. Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### 2. Create Domain Configuration
```bash
sudo nano /etc/nginx/sites-available/royalprompts.online
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name royalprompts.online www.royalprompts.online;

    location / {
        proxy_pass http://localhost:4321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:4321/health;
        proxy_set_header Host $host;
    }
}
```

### 3. Enable the Site
```bash
sudo ln -s /etc/nginx/sites-available/royalprompts.online /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 HTTPS Setup (Optional but Recommended)

To add SSL/HTTPS support:

### 1. Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Get SSL Certificate
```bash
sudo certbot --nginx -d royalprompts.online -d www.royalprompts.online
```

### 3. Update Astro Config
Update `landing/astro.config.mjs`:
```javascript
site: 'https://royalprompts.online',
```

## 🐛 Troubleshooting

### Domain Not Working
1. Check DNS propagation: `nslookup royalprompts.online`
2. Verify Nginx is running: `sudo systemctl status nginx`
3. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`

### Landing Page Not Loading
1. Check if container is running: `docker ps | grep royalprompts_landing`
2. Check container logs: `docker logs royalprompts_landing`
3. Test port 4321 directly: `curl http://localhost:4321`

### Nginx Configuration Issues
1. Test configuration: `sudo nginx -t`
2. Check syntax: `sudo nginx -T`
3. Reload Nginx: `sudo systemctl reload nginx`

## 📊 Final Result

After setup, your users can access:
- ✅ `http://royalprompts.online` → Landing page
- ✅ `http://royalprompts.online/privacy` → Privacy page
- ✅ `http://royalprompts.online/terms` → Terms page
- ✅ `http://royalprompts.online/about` → About page
- ✅ `http://royalprompts.online/contact` → Contact page
- ✅ `http://royalprompts.online/admin` → Admin panel
- ✅ `http://royalprompts.online/api` → Backend API

## 🔄 CI/CD Integration

The domain setup is now integrated with your CI/CD pipeline. When you push changes to the `landing/` directory, the deployment will automatically use the new domain configuration.

## 📝 Notes

- The domain configuration is stored in `/etc/nginx/sites-available/royalprompts.online`
- Nginx acts as a reverse proxy, forwarding requests to your Docker container
- The setup supports both `royalprompts.online` and `www.royalprompts.online`
- Health checks are available at `http://royalprompts.online/health`
