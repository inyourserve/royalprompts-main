# 🚀 RoyalPrompts - Single Droplet Deployment Guide

This guide will help you deploy the complete RoyalPrompts application (Backend + Frontend + Database) on a single DigitalOcean droplet.

## 📋 Prerequisites

- DigitalOcean Droplet (Ubuntu 20.04+ recommended)
- Domain name pointing to your droplet
- SSH access to your droplet
- **MongoDB Atlas account** (free tier) with cluster created

## 🛠️ Server Setup

### 1. Connect to your DigitalOcean Droplet

```bash
ssh root@your-droplet-ip
```

### 2. Create a non-root user (recommended)

```bash
# Create user
adduser royalprompts
usermod -aG sudo royalprompts

# Switch to the new user
su - royalprompts
```

### 3. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply group changes
exit
ssh royalprompts@your-droplet-ip
```

### 4. Install additional tools

```bash
# Install curl and other utilities
sudo apt install -y curl wget git unzip

# Install Node.js (for any manual operations)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 📦 Application Deployment

### 1. Clone the repository

```bash
# Clone the repository
git clone https://github.com/your-username/royalprompts.git
cd royalprompts

# Or upload your project files using SCP/SFTP
```

### 2. Set up MongoDB Atlas

1. **Create MongoDB Atlas Account** (if you haven't already):
   - Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Sign up for free account
   - Create a new cluster (M0 Sandbox is free)

2. **Configure Database Access**:
   - Go to "Database Access" in Atlas dashboard
   - Create a database user with read/write permissions
   - Note down username and password

3. **Configure Network Access**:
   - Go to "Network Access" in Atlas dashboard
   - Add IP address `0.0.0.0/0` (allow from anywhere) for development
   - For production, add your DigitalOcean droplet IP

4. **Get Connection String**:
   - Go to "Clusters" → "Connect" → "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Replace `<dbname>` with `royalprompts`

### 3. Configure environment variables

```bash
# Copy the example environment file
cp env.production.example .env

# Edit the environment file
nano .env
```

**Important environment variables to update:**

```bash
# Security (CRITICAL - Change these!)
SECRET_KEY=your-super-secret-production-key-change-this-to-something-random-and-secure

# MongoDB Atlas (CRITICAL - Use your Atlas connection string!)
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/royalprompts?retryWrites=true&w=majority

# Domain configuration
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

### 4. Deploy the application

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The deployment script will:
- ✅ Check prerequisites
- ✅ Create necessary directories
- ✅ Build Docker images
- ✅ Start all services
- ✅ Check service health
- ✅ Display status and next steps

## 🌐 Domain and SSL Setup

### 1. Configure DNS

Point your domain to your DigitalOcean droplet:
- A record: `yourdomain.com` → `your-droplet-ip`
- A record: `www.yourdomain.com` → `your-droplet-ip`

### 2. Set up SSL with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx container temporarily
docker-compose -f docker-compose.production.yml stop nginx

# Generate SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem

# Update nginx configuration for HTTPS
# Uncomment the HTTPS server block in nginx/nginx.conf

# Restart nginx
docker-compose -f docker-compose.production.yml up -d nginx
```

### 3. Set up automatic SSL renewal

```bash
# Add cron job for automatic renewal
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /home/royalprompts/royalprompts/docker-compose.production.yml restart nginx
```

## 🔧 Management Commands

### View logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f frontend
docker-compose -f docker-compose.production.yml logs -f nginx
```

### Restart services
```bash
# All services
docker-compose -f docker-compose.production.yml restart

# Specific service
docker-compose -f docker-compose.production.yml restart backend
```

### Update application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.production.yml up --build -d
```

### Backup database (MongoDB Atlas)
```bash
# Create backup from MongoDB Atlas
./start.sh backup

# Or manually:
docker-compose -f docker-compose.production.yml exec -T backend mongodump --uri="$MONGODB_URL" --out /tmp/backup
docker cp royalprompts_backend:/tmp/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Monitor resources
```bash
# Check container resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose.production.yml logs
   
   # Check if ports are in use
   sudo netstat -tlnp | grep :80
   sudo netstat -tlnp | grep :8000
   ```

2. **Database connection issues (MongoDB Atlas)**
   ```bash
   # Check backend logs for MongoDB Atlas connection
   docker-compose -f docker-compose.production.yml logs backend
   
   # Test MongoDB Atlas connection
   docker-compose -f docker-compose.production.yml exec backend python -c "
   from app.db.database import init_beanie
   import asyncio
   asyncio.run(init_beanie())
   print('MongoDB Atlas connection successful!')
   "
   ```

3. **File upload issues**
   ```bash
   # Check upload directory permissions
   ls -la uploads/
   
   # Check nginx logs
   docker-compose -f docker-compose.production.yml logs nginx
   ```

4. **SSL certificate issues**
   ```bash
   # Check certificate validity
   openssl x509 -in nginx/ssl/cert.pem -text -noout
   
   # Test SSL
   curl -I https://yourdomain.com
   ```

### Performance Optimization

1. **Enable gzip compression** (already configured in nginx.conf)
2. **Configure CDN** for static assets (optional)
3. **Set up monitoring** with tools like Prometheus + Grafana (optional)
4. **Optimize images** before upload (recommended)

## 📊 Monitoring and Maintenance

### Health Checks
- Backend: `http://yourdomain.com/api/health`
- Frontend: `http://yourdomain.com`
- Nginx: `http://yourdomain.com/health`

### Regular Maintenance
- Monitor disk space: `df -h`
- Check container health: `docker-compose -f docker-compose.production.yml ps`
- Review logs regularly
- Update dependencies monthly
- Backup database weekly

## 🔒 Security Considerations

1. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **Regular Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose -f docker-compose.production.yml pull
   docker-compose -f docker-compose.production.yml up -d
   ```

3. **Backup Strategy**
   - Database backups (daily)
   - Upload files backup (daily)
   - Configuration backup (weekly)

## 📞 Support

If you encounter any issues:
1. Check the logs first
2. Review this documentation
3. Check GitHub issues
4. Contact support

---

**🎉 Congratulations!** Your RoyalPrompts application should now be running on your DigitalOcean droplet with:
- ✅ FastAPI Backend
- ✅ Next.js Admin Panel
- ✅ MongoDB Atlas (Cloud Database)
- ✅ Nginx Reverse Proxy
- ✅ SSL/HTTPS Support
- ✅ File Upload Handling
- ✅ Health Monitoring
