# 🚀 Manual Deployment Guide

## Understanding the Railway 404 Error

### Root Cause
Railway has evolved their deployment system:
- **Old System**: Accepted GitHub URLs directly via `/new/template?template=GITHUB_URL`
- **Current System**: Requires either GitHub integration or pre-registered template IDs
- **Domain Change**: Some endpoints moved from `railway.app` to `railway.com`

### Why Your URL Failed
```
https://railway.com/new/template?template=https://github.com/mh2010github/webcam/tree/deploy
```
This URL format is deprecated. The `/new/template` endpoint no longer exists.

## ✅ Correct Deployment Methods

### Method 1: Railway via GitHub (Recommended)

1. **Go to Railway's GitHub deployment page:**
   ```
   https://railway.app/new/github
   ```

2. **Connect your GitHub account**

3. **Select your repository:**
   - Repository: `mh2010github/webcam`
   - Branch: `deploy`

4. **Deploy:**
   - Railway auto-detects the app configuration
   - Uses `railway.json` for settings
   - Deploys with automatic HTTPS

### Method 2: Render Deployment (Alternative)

1. **Use this deployment URL:**
   ```
   https://render.com/deploy?repo=https://github.com/mh2010github/webcam&branch=deploy
   ```

2. **Benefits:**
   - `render.yaml` already configured
   - Free tier with automatic HTTPS
   - No credit card required

### Method 3: Deploy Button for README

Add this to your README.md:
```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/github/mh2010github/webcam?branch=deploy)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/mh2010github/webcam&branch=deploy)
```

## 📋 Post-Deployment Checklist

### 1. Verify Endpoints
```bash
# Health check
curl -s https://your-app.railway.app/health | jq .

# System info
curl -s https://your-app.railway.app/api/info | jq .

# Metrics
curl -s https://your-app.railway.app/api/metrics | jq .

# Fatigue analysis
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"perclos": 0.25, "confidence": 0.95}' \
  https://your-app.railway.app/api/analyze | jq .
```

### 2. Test ChatGPT Compatibility
- ✅ HTTPS enabled automatically
- ✅ CORS headers configured
- ✅ JSON responses
- ✅ No authentication required

### 3. Run Validation Script
```bash
python3 validate_deployment.py https://your-app.railway.app
```

## 🔧 Troubleshooting

### Railway Deployment Issues
- **Build fails**: Check `requirements.txt` has all dependencies
- **App crashes**: Verify `PORT` environment variable usage
- **404 on endpoints**: Ensure `app.py` is in root directory

### Render Deployment Issues
- **Slow cold starts**: Normal for free tier (spins down after 15 min)
- **Build timeout**: Split large dependencies if needed
- **Domain issues**: Use provided `.onrender.com` domain

## 🎯 Quick Deploy Commands

### Local Testing First
```bash
# Test locally
python3 app.py

# Validate endpoints
python3 validate_deployment.py http://localhost:5000
```

### Push to Deploy Branch
```bash
git checkout deploy
git merge master
git push origin deploy
```

### Monitor Deployment
- Railway: Check build logs in dashboard
- Render: View deploy logs in dashboard

## 🚨 Important Notes

1. **Free Tier Limits:**
   - Railway: $5 credit/month
   - Render: Spins down after 15 min inactivity

2. **Production Recommendations:**
   - Use environment variables for sensitive data
   - Enable health check monitoring
   - Set up custom domain if needed

3. **ChatGPT Agent Requirements Met:**
   - ✅ HTTPS automatic
   - ✅ CORS enabled
   - ✅ No authentication
   - ✅ JSON responses
   - ✅ Public endpoints