# 🚀 RoyalPrompts CI/CD Setup with Your `royalprompt` Key

You've already created the perfect SSH key for this project! Here's how to set up CI/CD with your `royalprompt` key.

## 🔑 Your SSH Key Details

**Public Key (already added to your droplet):**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII7jnKZzo/0nLAqc3Te+kTRAdmEWi5l3laC6bSbIIjd4 vikash@vikashs-MacBook-Air.local
```

**Private Key Location:** `~/royalprompt`

## 📋 GitHub Secrets Setup

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these 4 secrets:

### 1. DROPLET_HOST
```
[Your droplet IP address]
```

### 2. DROPLET_USERNAME
```
root
```

### 3. DROPLET_PORT
```
22
```

### 4. DROPLET_SSH_KEY
Copy this entire private key content:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCO45ymc6P9JywKnN03vpE0QHZhFouZd5Wgum0myCI3eAAAAKj9guz5/YLs
+QAAAAtzc2gtZWQyNTUxOQAAACCO45ymc6P9JywKnN03vpE0QHZhFouZd5Wgum0myCI3eA
AAAEDJPVUshBvSpHqDD/RPoEwYJRm7aTQOQTla39Gp5++Ho47jnKZzo/0nLAqc3Te+kTRA
dmEWi5l3laC6bSbIIjd4AAAAIHZpa2FzaEB2aWthc2hzLU1hY0Jvb2stQWlyLmxvY2FsAQ
IDBAU=
-----END OPENSSH PRIVATE KEY-----
```

## 🚀 Quick Setup Steps

### 1. Test SSH Connection
```bash
# Test with your royalprompt key
ssh -i ~/royalprompt root@your-droplet-ip
```

### 2. Add GitHub Secrets
- Go to your GitHub repo → Settings → Secrets → Actions
- Add the 4 secrets listed above

### 3. Update Environment Variables
```bash
# Edit your .env file
nano .env
```

**Important variables to update:**
```bash
# MongoDB Atlas (CRITICAL - Use your Atlas connection string!)
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/royalprompts?retryWrites=true&w=majority

# Security (CRITICAL - Generate a secure random key!)
SECRET_KEY=your-super-secret-production-key-change-this-to-something-random-and-secure

# Domain configuration
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

### 4. Push to GitHub
```bash
git add .
git commit -m "Add CI/CD pipeline for backend"
git push origin main
```

## 🎯 What Happens Next

1. **Push to `main`** → Triggers automatic deployment
2. **CI/CD Pipeline runs:**
   - ✅ Code quality checks
   - ✅ Security scanning
   - ✅ Docker image build
   - ✅ Deploy to your droplet
   - ✅ Health checks and rollback

3. **Monitor deployment:**
   - Go to GitHub Actions tab
   - Watch the workflow execution
   - Check deployment logs

## 🔍 Testing Your Setup

### Test SSH Connection
```bash
ssh -i ~/royalprompt root@your-droplet-ip "echo 'SSH connection successful'"
```

### Test Deployment
```bash
# After pushing to GitHub, check the Actions tab
# Or manually trigger: Actions → Run workflow
```

## 🛠️ Troubleshooting

### SSH Issues
```bash
# If SSH asks for password, your key isn't loaded
ssh-add ~/royalprompt

# Test connection
ssh -i ~/royalprompt root@your-droplet-ip
```

### GitHub Secrets Issues
- Double-check secret names (case-sensitive)
- Ensure no extra spaces or newlines
- Verify private key is complete

### Deployment Issues
- Check GitHub Actions logs
- Verify .env file configuration
- Check MongoDB Atlas connection

## 📊 CI/CD Features

Your setup includes:

- ✅ **Automated Testing** - Code quality and security checks
- ✅ **Docker Build** - Creates optimized production images
- ✅ **Secure Deployment** - Uses your SSH key for server access
- ✅ **Health Monitoring** - Verifies deployment success
- ✅ **Automatic Rollback** - Reverts on failure
- ✅ **Multi-Environment** - Staging and production support

## 🎉 Ready to Deploy!

1. ✅ Add GitHub secrets (listed above)
2. ✅ Update .env file with your MongoDB Atlas URL
3. ✅ Push to GitHub
4. ✅ Watch the magic happen! 🚀

---

**Your `royalprompt` key is perfect for this project!** 🎯

