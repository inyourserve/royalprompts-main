# 🔐 GitHub Secrets Setup Guide

Since you already have SSH access to your DigitalOcean droplet, here's how to set up the GitHub secrets for CI/CD:

## 📋 Required GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

### 1. DROPLET_HOST
```
Your droplet IP address (e.g., 164.90.123.456)
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
Copy your private SSH key content. Run this command to get it:

```bash
cat ~/.ssh/id_ed25519
```

**Important:** Copy the ENTIRE content including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
[your key content]
-----END OPENSSH PRIVATE KEY-----
```

## 🚀 Quick Setup

### Option 1: Use the Setup Script
```bash
./scripts/setup-cicd-existing-key.sh
```

### Option 2: Manual Setup

1. **Get your droplet IP:**
   ```bash
   # If you don't know it, check your DigitalOcean dashboard
   ```

2. **Get your private key:**
   ```bash
   cat ~/.ssh/id_ed25519
   ```

3. **Add GitHub secrets:**
   - Go to your GitHub repo → Settings → Secrets → Actions
   - Add each secret with the values above

4. **Create .env file:**
   ```bash
   cp env.production.example .env
   # Edit .env with your MongoDB Atlas URL and other settings
   ```

5. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add CI/CD pipeline"
   git push origin main
   ```

## 🔍 Testing Your Setup

After adding the secrets, you can test the CI/CD by:

1. **Push to main branch** - Triggers automatic deployment
2. **Manual trigger** - Go to Actions tab → Run workflow
3. **Check deployment logs** - View the workflow execution

## 🛠️ Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connection manually
ssh root@your-droplet-ip

# If it asks for password, your key isn't loaded
ssh-add ~/.ssh/id_ed25519
```

### Private Key Format Issues
Make sure your private key includes the header and footer:
```
-----BEGIN OPENSSH PRIVATE KEY-----
[content]
-----END OPENSSH PRIVATE KEY-----
```

### GitHub Secrets Not Working
- Double-check the secret names (case-sensitive)
- Ensure no extra spaces or newlines
- Verify the private key is complete

## 📊 What Happens After Setup

1. **Push to main** → CI/CD runs automatically
2. **Tests run** → Code quality and security checks
3. **Docker build** → Creates and pushes image to GitHub Container Registry
4. **Deploy** → SSH to your droplet and updates the backend
5. **Health check** → Verifies deployment and rolls back if needed

## 🎯 Next Steps

1. ✅ Add GitHub secrets
2. ✅ Update .env file
3. ✅ Push to GitHub
4. ✅ Watch the magic happen! 🚀

---

**Need help?** Check the CI/CD logs in GitHub Actions for detailed error messages.
