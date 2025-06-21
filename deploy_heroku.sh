#!/bin/bash
# Heroku Deployment Script for Fatigue Detection System

echo "🚀 HEROKU DEPLOYMENT SCRIPT"
echo "=" * 50

# Login to Heroku (you'll need to do this step)
echo "📝 Step 1: Login to Heroku"
echo "Run: heroku login"
echo "Press Enter when logged in..."
read

# Create Heroku app
echo "📦 Step 2: Creating Heroku app..."
APP_NAME="fatigue-detection-$(date +%s)"
heroku create $APP_NAME

# Set Python runtime
echo "🐍 Step 3: Setting Python runtime..."
echo "python-3.10.12" > runtime.txt
git add runtime.txt

# Deploy to Heroku
echo "🚀 Step 4: Deploying to Heroku..."
git add -A
git commit -m "🚀 Heroku deployment ready" || echo "No changes to commit"
git push heroku master

# Open the app
echo "🌐 Step 5: Opening deployed app..."
heroku open

# Show app info
echo "✅ DEPLOYMENT COMPLETE!"
echo "Your app URL: https://$APP_NAME.herokuapp.com"
echo "Health check: https://$APP_NAME.herokuapp.com/health"

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10
curl "https://$APP_NAME.herokuapp.com/health"