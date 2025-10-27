# 🚨 Disaster Recovery Procedures

## Quick Recovery Decision Tree

```
Is the service down?
├─ Yes → Go to "Immediate Actions"
└─ No → Is it degraded?
    ├─ Yes → Go to "Performance Issues"
    └─ No → Monitor normally
```

## 🔥 Immediate Actions (Service Down)

### 1. Check Platform Status
- **Railway**: https://status.railway.app
- **Render**: https://status.render.com
- **Fly.io**: https://status.fly.io

### 2. Quick Diagnostics
```bash
# Test all endpoints
curl -I https://your-app.railway.app/health

# Check DNS
nslookup your-app.railway.app

# Test from different location
curl -I https://your-app.railway.app/health --connect-timeout 5
```

### 3. Immediate Recovery Actions

#### Option A: Restart Service
**Railway:**
```bash
# Via dashboard: Click "Restart" in service settings
```

**Render:**
```bash
# Via dashboard: Settings → Manual Deploy → "Deploy"
```

**Fly.io:**
```bash
fly apps restart fatigue-detection-system
```

#### Option B: Rollback Deployment
**Railway:**
- Dashboard → Deployments → Click previous deployment → "Rollback"

**Render:**
- Dashboard → Events → Find previous deploy → "Rollback"

**Fly.io:**
```bash
fly releases
fly deploy --image [previous-image-id]
```

## 🔄 Failover Procedures

### Scenario 1: Primary Platform Down

1. **Verify primary is down:**
   ```bash
   python3 validate_live_deployment.py https://primary-app.railway.app
   ```

2. **Deploy to backup platform:**
   ```bash
   # If Railway is down, deploy to Render:
   git checkout deploy
   git push render deploy:main
   
   # Or deploy to Fly.io:
   fly deploy
   ```

3. **Update DNS/Links:**
   - Update any hardcoded URLs
   - Notify users of temporary URL change

### Scenario 2: Regional Outage

1. **Deploy to different region:**
   ```bash
   # Fly.io multi-region
   fly regions add lax  # Add Los Angeles
   fly scale count 2    # Scale across regions
   ```

## 🐛 Common Issues & Fixes

### 1. 502 Bad Gateway
**Cause**: App crashed or not responding
**Fix**:
```bash
# Check logs
fly logs  # or Railway/Render dashboard

# Common fixes:
- Ensure PORT env var is used
- Check memory limits
- Verify requirements.txt
```

### 2. Build Failures
**Cause**: Missing dependencies or syntax errors
**Fix**:
```bash
# Test locally first
python3 -m pip install -r requirements.txt
python3 app.py

# Check for syntax errors
python3 -m py_compile app.py
```

### 3. CORS Issues
**Cause**: Flask-CORS misconfiguration
**Fix**:
```python
# Verify in app.py:
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # This should allow all origins
```

### 4. Memory/CPU Limits
**Railway/Render**: Usually auto-scales
**Fly.io**:
```bash
# Scale up if needed
fly scale vm shared-cpu-2x
fly scale memory 512
```

## 📊 Monitoring & Alerts

### Set Up Monitoring
1. **UptimeRobot** (Free):
   - Add monitor for https://your-app.railway.app/health
   - Set check interval: 5 minutes
   - Alert via email/SMS

2. **Custom Monitor**:
   ```bash
   # Run continuous monitor
   python3 monitor_deployment.py https://your-app.railway.app 60
   ```

### Health Check Script
```bash
#!/bin/bash
# save as health_check.sh

URL="https://your-app.railway.app/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -ne 200 ]; then
    echo "ALERT: Service down! Status: $RESPONSE"
    # Send alert (email, Slack, etc.)
fi
```

## 🔧 Recovery Validation

After any recovery action:

1. **Run full validation:**
   ```bash
   python3 validate_live_deployment.py https://recovered-app.com
   ```

2. **Test critical endpoints:**
   ```bash
   # Health
   curl https://recovered-app.com/health
   
   # Analysis
   curl -X POST -H 'Content-Type: application/json' \
     -d '{"perclos": 0.25, "confidence": 0.95}' \
     https://recovered-app.com/api/analyze
   ```

3. **Monitor for 15 minutes:**
   ```bash
   python3 monitor_deployment.py https://recovered-app.com 15
   ```

## 📋 Incident Response Checklist

- [ ] Identify the issue (down/degraded/error)
- [ ] Check platform status pages
- [ ] Review recent deployments
- [ ] Check application logs
- [ ] Attempt restart/rollback
- [ ] Deploy to backup platform if needed
- [ ] Validate recovery
- [ ] Monitor for stability
- [ ] Document incident and resolution

## 🔐 Backup Strategies

### 1. Multi-Platform Deployment
Always maintain deployments on:
- Primary: Railway
- Backup: Render
- Emergency: Fly.io

### 2. Code Backups
```bash
# Regular backups
git push origin deploy
git tag -a "stable-$(date +%Y%m%d)" -m "Stable release"
git push --tags
```

### 3. Configuration Backups
Keep copies of:
- requirements.txt
- railway.json
- render.yaml
- fly.toml
- Deployment URLs and credentials

## 📞 Escalation Path

1. **Level 1**: Automated monitoring alerts
2. **Level 2**: Manual intervention (restart/rollback)
3. **Level 3**: Platform migration (failover)
4. **Level 4**: Platform support tickets

## 🚀 Quick Deploy Commands

```bash
# Railway (via GitHub integration)
# Go to: https://railway.app/dashboard

# Render
git push render deploy:main

# Fly.io
fly deploy

# Local testing
python3 app.py
```

Remember: **Stay calm, follow the procedures, and validate each step!**