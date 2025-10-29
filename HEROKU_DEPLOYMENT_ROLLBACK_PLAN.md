# Heroku Deployment Plan with Instant Rollback

## Overview
This plan ensures we can deploy the reorganized code to Heroku with the ability to instantly rollback if issues arise.

## Current Stable State
- **Current Branch**: master (working in production)
- **Heroku App**: xcellerate-eq-4f2dd61b4bbd
- **Last Known Good Commit**: 9e3b82ad (tagged as STABLE)

## Pre-Deployment Checklist

### 1. Document Current State
```bash
# Record current Heroku release
heroku releases -a xcellerate-eq-4f2dd61b4bbd | head -5

# Note the current release version (e.g., v123)
CURRENT_RELEASE=v[NUMBER]

# Tag current production state
git checkout master
git tag pre-cleanup-deploy
git push origin pre-cleanup-deploy
```

### 2. Create Heroku Review App (Safest Option)
```bash
# Create a review app for testing
heroku create xcellerate-eq-cleanup-test --region us

# Deploy cleanup branch to test app
git push heroku cleanup:main

# Test all endpoints
curl https://xcellerate-eq-cleanup-test.herokuapp.com/health
curl https://xcellerate-eq-cleanup-test.herokuapp.com/rtms/ui
```

## Deployment Options

### Option A: Using Heroku Pipeline Promotion (Recommended)
1. Create a staging app in the pipeline
2. Deploy cleanup branch to staging
3. Test thoroughly
4. Promote to production with one click
5. Rollback is instant via Heroku dashboard

### Option B: Direct Deploy with Git (Faster but Riskier)
```bash
# Deploy cleanup branch to production
git push heroku cleanup:main

# Monitor logs immediately
heroku logs --tail -a xcellerate-eq-4f2dd61b4bbd
```

## Instant Rollback Methods

### Method 1: Heroku Release Rollback (Fastest - 30 seconds)
```bash
# If issues arise, rollback to previous release
heroku rollback v[PREVIOUS_RELEASE_NUMBER] -a xcellerate-eq-4f2dd61b4bbd

# Verify rollback
heroku releases -a xcellerate-eq-4f2dd61b4bbd
```

### Method 2: Git Force Push (1-2 minutes)
```bash
# Force push master branch back
git checkout master
git push heroku master:main --force

# This overwrites with the stable master branch
```

### Method 3: Using Tagged Release (1-2 minutes)
```bash
# Push the pre-deployment tag
git push heroku pre-cleanup-deploy:main --force
```

## Deployment Script with Auto-Rollback

Create `deploy-with-rollback.sh`:
```bash
#!/bin/bash
set -e

APP_NAME="xcellerate-eq-4f2dd61b4bbd"
HEALTH_CHECK_URL="https://$APP_NAME.herokuapp.com/health"
RTMS_CHECK_URL="https://$APP_NAME.herokuapp.com/rtms/ui"

# Get current release number
echo "📝 Recording current release..."
CURRENT_RELEASE=$(heroku releases -a $APP_NAME --json | jq -r '.[0].version')
echo "Current release: $CURRENT_RELEASE"

# Deploy
echo "🚀 Deploying cleanup branch..."
git push heroku cleanup:main

# Wait for app to restart
echo "⏳ Waiting for app to restart (30 seconds)..."
sleep 30

# Health checks
echo "🏥 Running health checks..."
if ! curl -f -s -o /dev/null "$HEALTH_CHECK_URL"; then
    echo "❌ Health check failed! Rolling back..."
    heroku rollback $CURRENT_RELEASE -a $APP_NAME
    exit 1
fi

if ! curl -f -s -o /dev/null "$RTMS_CHECK_URL"; then
    echo "❌ RTMS check failed! Rolling back..."
    heroku rollback $CURRENT_RELEASE -a $APP_NAME
    exit 1
fi

echo "✅ Deployment successful! All checks passed."
```

## Post-Deployment Verification

### Critical Endpoints to Test
1. Main app: https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/
2. RTMS UI: https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/rtms/ui
3. Analytics: https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/test-analytics
4. API health: https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/health

### Monitoring Commands
```bash
# Watch logs
heroku logs --tail -a xcellerate-eq-4f2dd61b4bbd

# Check dyno status
heroku ps -a xcellerate-eq-4f2dd61b4bbd

# View recent errors
heroku logs -a xcellerate-eq-4f2dd61b4bbd --source app --dyno web | grep ERROR
```

## Risk Mitigation

### Known Risks
1. **Import Path Changes**: All imports now use `src.` prefix
2. **Static File Paths**: Flask configured with new paths
3. **Procfile Commands**: Updated to reference new locations

### Mitigation Steps
1. Extensive testing on cleanup branch completed ✅
2. All components verified to import correctly ✅
3. Procfile commands tested ✅

## Emergency Contacts & Resources
- Heroku Status: https://status.heroku.com/
- Release History: `heroku releases -a xcellerate-eq-4f2dd61b4bbd`
- Current Logs: `heroku logs -a xcellerate-eq-4f2dd61b4bbd`

## Recommended Deployment Window
- Deploy during low-traffic period
- Have 15-30 minutes available for testing
- Keep this document open for quick reference

## Go/No-Go Decision Points
✅ All tests pass on cleanup branch locally
✅ Heroku review app works correctly
✅ Rollback plan understood and tested
✅ Monitoring in place
⏳ Deploy to production

## Quick Rollback Command
If anything goes wrong, run:
```bash
heroku rollback -a xcellerate-eq-4f2dd61b4bbd
```
This takes effect in ~30 seconds.