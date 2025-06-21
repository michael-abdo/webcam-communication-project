# 🚀 Heroku VM Deployment Guide

## Issue: IP Address Mismatch in VM

When deploying from a VM, Heroku's browser-based login doesn't work due to IP mismatches.

## Solution 1: Interactive Login

```bash
heroku login -i
```

Then enter:
- Email: your-email@example.com
- Password: your-heroku-password

## Solution 2: API Token (Recommended for VMs)

1. **Get API Token**:
   - Go to: https://dashboard.heroku.com/account
   - Scroll to "API Key"
   - Click "Reveal" and copy the token

2. **Set Token Locally**:
   ```bash
   heroku auth:token
   # Paste your API token when prompted
   ```

3. **Or set environment variable**:
   ```bash
   export HEROKU_API_KEY=your-api-token-here
   ```

## Solution 3: Deploy via GitHub (Easiest)

1. **Enable GitHub Integration**:
   - Go to: https://dashboard.heroku.com/new
   - Click "Connect to GitHub"
   - Search for: michael-abdo/webcam-communication-project
   - Select branch: master
   - Click "Deploy Branch"

## Solution 4: Manual App Creation

If login issues persist:

```bash
# 1. Create app via web dashboard
# Go to: https://dashboard.heroku.com/new
# App name: fatigue-detection-api

# 2. Add Heroku remote manually
git remote add heroku https://git.heroku.com/fatigue-detection-api.git

# 3. Deploy
git push heroku master
```

## Quick Commands Once Logged In

```bash
# Create app
heroku create fatigue-detection-api

# Deploy
git push heroku master

# Open app
heroku open

# Check logs
heroku logs --tail
```

## Expected Result

Your app will be live at:
```
https://fatigue-detection-api.herokuapp.com
```

## Alternative: Use Heroku Web Dashboard

1. Go to: https://dashboard.heroku.com/new
2. Connect to GitHub
3. Select: michael-abdo/webcam-communication-project
4. Deploy branch: master
5. Click "Deploy"

This avoids all CLI login issues!