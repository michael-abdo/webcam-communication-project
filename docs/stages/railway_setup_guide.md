# 🚂 Railway Account Setup Guide

## Step-by-Step Railway Deployment Instructions

### Phase 1: Account Creation
1. **Visit Railway**: Go to [railway.app](https://railway.app)
2. **Sign Up**: Click "Sign up" and choose "Continue with GitHub"
3. **Authorize**: Grant Railway access to your GitHub repositories
4. **Verify Email**: Check your email and verify your Railway account

### Phase 2: Repository Preparation
1. **Fork Repository**: 
   - Go to: https://github.com/michael-abdo/webcam-communication-project
   - Click "Fork" to create your own copy
   - Ensure the `deploy` branch is available in your fork

2. **Verify Deploy Branch**:
   - In your forked repository, check that `deploy` branch exists
   - This branch contains all deployment configurations

### Phase 3: Railway Project Creation
1. **Create New Project**:
   - In Railway dashboard, click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository
   - Select the `deploy` branch

2. **Configuration Verification**:
   - Railway will auto-detect `railway.json`
   - Verify these settings are detected:
     - Build command: `pip install -r requirements.txt`
     - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
     - Health check: `/health`

### Phase 4: Environment Variables (Auto-configured)
Railway automatically sets:
- `PORT`: Application port (auto-assigned)
- `RAILWAY_ENVIRONMENT`: `production`

No manual environment variables needed for basic deployment.

### Phase 5: Deployment Process
1. **Deploy**: Click "Deploy" in Railway dashboard
2. **Monitor**: Watch build logs for any errors
3. **Wait**: Initial deployment takes 2-3 minutes
4. **Access**: Railway provides a public URL: `https://your-app-name.railway.app`

### Phase 6: Verification Commands
Once deployed, run these validation commands:

```bash
# Replace YOUR_APP_URL with your actual Railway URL
export RAILWAY_URL="https://your-app-name.railway.app"

# Test health endpoint
curl -s $RAILWAY_URL/health | jq .

# Test system info
curl -s $RAILWAY_URL/api/info | jq .

# Test fatigue analysis
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"perclos": 0.25, "confidence": 0.95}' \
  $RAILWAY_URL/api/analyze | jq .

# Run comprehensive validation
python3 validate_deployment.py $RAILWAY_URL
```

### Expected Results
✅ **Automatic HTTPS**: Railway provides SSL certificates  
✅ **Public Access**: No authentication required  
✅ **CORS Enabled**: ChatGPT agent compatible  
✅ **Health Monitoring**: Automatic restart on failures  
✅ **Performance**: Sub-100ms response times  

### Troubleshooting
**Build Failures:**
- Check that `requirements.txt` includes all dependencies
- Verify Python version in `runtime.txt` is supported
- Review build logs for specific error messages

**502 Bad Gateway:**
- Wait 30-60 seconds for cold start
- Check health endpoint: `/health`
- Verify gunicorn is starting correctly

**Connection Issues:**
- Ensure CORS headers are present
- Verify JSON responses on all endpoints
- Test with curl before browser testing

### Next Steps After Setup
1. Note your Railway URL
2. Run validation tests
3. Proceed with Render deployment as backup
4. Configure monitoring and alerts