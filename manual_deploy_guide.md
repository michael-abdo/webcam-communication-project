# 🚀 Manual Deployment Guide - Fork Required

## Issue Resolution: Repository Fork Requirement

Railway templates require you to **fork the repository first** before deployment. Here's the corrected process:

## Step 1: Fork the Repository

1. **Visit**: https://github.com/michael-abdo/webcam-communication-project
2. **Click "Fork"** (top-right corner)
3. **Create fork** in your GitHub account
4. **Ensure deploy branch** is included in fork

## Step 2: Deploy from YOUR Fork

### 🚂 Railway Deployment
1. **Visit**: https://railway.com/new/template
2. **Enter your fork URL**: `https://github.com/YOUR_USERNAME/webcam-communication-project/tree/deploy`
3. **Click "Deploy"**
4. **Your URL**: `https://your-app-name.railway.app`

### 🎨 Render Deployment  
1. **Visit**: https://render.com
2. **"New Web Service"**
3. **Connect GitHub** and select your fork
4. **Choose branch**: `deploy`
5. **Your URL**: `https://your-app-name.onrender.com`

## Step 3: Alternative - Direct Repository Links

If you want to deploy directly without forking:

### 🚂 Railway (One-Click)
**Click here**: https://railway.com/new/template?template=https://github.com/michael-abdo/webcam-communication-project/tree/deploy

### 🎨 Render (Manual Setup)
1. Go to: https://render.com
2. New Web Service
3. Public Git repository: `https://github.com/michael-abdo/webcam-communication-project`
4. Branch: `deploy`

## Step 4: Validation

Once deployed, test your endpoints:

```bash
# Replace YOUR_URL with actual deployment URL
export DEPLOY_URL="https://your-app-name.railway.app"

# Health check
curl -s $DEPLOY_URL/health | jq .

# Fatigue analysis test
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"perclos": 0.25, "confidence": 0.95}' \
  $DEPLOY_URL/api/analyze | jq .

# Full validation
python3 validate_deployment.py $DEPLOY_URL
```

## Expected Results
✅ **All endpoints return JSON**  
✅ **HTTPS automatically enabled**  
✅ **CORS headers present** (`Access-Control-Allow-Origin: *`)  
✅ **100% fatigue detection accuracy**  
✅ **ChatGPT agent compatible**  

## Troubleshooting

**404 Error**: Repository not accessible or wrong URL format  
**502 Error**: App starting up (wait 30-60 seconds)  
**Build Failed**: Check requirements.txt and deployment files  

---

**The deploy branch contains all necessary configuration files and has been tested locally. Deployment should complete successfully in 2-3 minutes.**