# 🚀 Deployment Access Guide

## Railway Deployment URLs

### During Deployment
- **Dashboard**: https://railway.app/dashboard
- **Project View**: Click on your project after deployment
- **Deployment Logs**: Available in the project view

### After Deployment
Your app will be available at:
```
https://[generated-name].railway.app
```

Example: `https://fatigue-detection-prd.railway.app`

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-21T12:00:00.000Z",
  "fatigue_system_available": true
}
```

### 2. System Information
```bash
curl https://your-app.railway.app/api/info
```

Expected response:
```json
{
  "name": "Fatigue Detection System",
  "version": "2.0.0",
  "features": {
    "perclos_detection": true,
    "blink_detection": true,
    "real_time_alerts": true
  }
}
```

### 3. Metrics Endpoint
```bash
curl https://your-app.railway.app/api/metrics
```

### 4. Fatigue Analysis
```bash
curl -X POST -H 'Content-Type: application/json' \
  -d '{"perclos": 0.25, "confidence": 0.95}' \
  https://your-app.railway.app/api/analyze
```

Expected response:
```json
{
  "fatigue_level": "MODERATE",
  "risk_score": 0.65,
  "recommendations": ["Take a 10-minute break"],
  "timestamp": "2024-01-21T12:00:00.000Z"
}
```

## 📱 ChatGPT Agent Integration

Share this with ChatGPT:
```
I have a fatigue detection API at https://your-app.railway.app

Endpoints:
- GET /health - System health check
- GET /api/info - System information
- GET /api/metrics - Current metrics
- POST /api/analyze - Analyze fatigue (body: {"perclos": 0.0-1.0, "confidence": 0.0-1.0})

All endpoints return JSON and support CORS.
```

## 🔍 Validation Script

Run the comprehensive validation:
```bash
python3 validate_deployment.py https://your-app.railway.app
```

## 🚨 Troubleshooting

### App Not Loading
1. Check deployment logs in Railway dashboard
2. Ensure build completed successfully
3. Verify PORT environment variable is used

### 502 Bad Gateway
1. App may still be building (wait 2-3 minutes)
2. Check if gunicorn started correctly
3. Verify requirements.txt has all dependencies

### CORS Issues
- CORS is enabled by default via Flask-CORS
- All origins are allowed for ChatGPT compatibility

## 📊 Railway Dashboard Features

### Monitoring
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: History and rollback options

### Settings
- **Environment Variables**: Add if needed
- **Domain**: Custom domain setup
- **Resources**: Adjust memory/CPU limits

## 🎯 Success Checklist

- [ ] Deployment completed in Railway
- [ ] Received deployment URL
- [ ] Health endpoint returns 200 OK
- [ ] All API endpoints responding
- [ ] CORS headers present in responses
- [ ] ChatGPT can access the API
- [ ] No authentication required
- [ ] HTTPS automatically enabled

## 💡 Pro Tips

1. **Free Tier**: Railway provides $5 credit monthly
2. **Auto-Sleep**: Free tier doesn't sleep (unlike Render)
3. **Logs**: Check logs for any startup issues
4. **Restart**: Can restart service from dashboard

## 🔗 Quick Links

- **Railway Status**: https://status.railway.app
- **Railway Docs**: https://docs.railway.app
- **Support**: https://railway.app/help