#!/bin/bash

# Heroku Analytics Full Deployment Script
# This script sets up everything needed for talk time analytics on Heroku

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if app name is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide your Heroku app name${NC}"
    echo "Usage: ./deploy_analytics_heroku.sh your-app-name"
    exit 1
fi

APP_NAME=$1

echo -e "${GREEN}🚀 Starting full analytics deployment for $APP_NAME${NC}"

# 1. Check if logged in to Heroku
echo -e "\n${YELLOW}Checking Heroku login...${NC}"
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${RED}Not logged in to Heroku. Please run: heroku login${NC}"
    exit 1
fi

# 2. Add Redis addon if not already added
echo -e "\n${YELLOW}Checking Redis addon...${NC}"
if heroku addons:info heroku-redis -a $APP_NAME &> /dev/null; then
    echo -e "${GREEN}✓ Redis addon already exists${NC}"
else
    echo "Adding Redis addon..."
    heroku addons:create heroku-redis:mini -a $APP_NAME
    echo -e "${GREEN}✓ Redis addon added${NC}"
fi

# 3. Add Node.js buildpack for RTMS service
echo -e "\n${YELLOW}Checking buildpacks...${NC}"
BUILDPACKS=$(heroku buildpacks -a $APP_NAME)

if [[ ! $BUILDPACKS == *"heroku/nodejs"* ]]; then
    echo "Adding Node.js buildpack..."
    heroku buildpacks:add heroku/nodejs -a $APP_NAME
    echo -e "${GREEN}✓ Node.js buildpack added${NC}"
else
    echo -e "${GREEN}✓ Node.js buildpack already exists${NC}"
fi

if [[ ! $BUILDPACKS == *"heroku/python"* ]]; then
    echo "Adding Python buildpack..."
    heroku buildpacks:add heroku/python -a $APP_NAME
    echo -e "${GREEN}✓ Python buildpack added${NC}"
else
    echo -e "${GREEN}✓ Python buildpack already exists${NC}"
fi

# 4. Commit and deploy changes
echo -e "\n${YELLOW}Deploying latest code...${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Committing local changes..."
    git add -A
    git commit -m "Deploy analytics with worker process" || true
fi

# Push to Heroku
echo "Pushing to Heroku..."
git push heroku main || git push heroku master

# 5. Wait for deployment to complete
echo -e "\n${YELLOW}Waiting for deployment to complete...${NC}"
sleep 30

# 6. Create analytics database tables
echo -e "\n${YELLOW}Setting up analytics database tables...${NC}"
heroku run python analytics_services/setup_database.py -a $APP_NAME

# 7. Scale up dynos
echo -e "\n${YELLOW}Scaling up dynos...${NC}"

# Check current dyno configuration
echo "Current dyno configuration:"
heroku ps -a $APP_NAME

# Scale web dyno (should already be 1)
heroku ps:scale web=1 -a $APP_NAME
echo -e "${GREEN}✓ Web dyno scaled to 1${NC}"

# Scale RTMS service
heroku ps:scale rtms=1 -a $APP_NAME
echo -e "${GREEN}✓ RTMS service scaled to 1${NC}"

# Scale worker (analytics service)
heroku ps:scale worker=1 -a $APP_NAME
echo -e "${GREEN}✓ Worker (analytics) scaled to 1${NC}"

# 8. Verify everything is running
echo -e "\n${YELLOW}Verifying deployment...${NC}"
sleep 10

# Check dyno status
echo -e "\n${YELLOW}Dyno Status:${NC}"
heroku ps -a $APP_NAME

# Check recent logs
echo -e "\n${YELLOW}Recent logs (checking for errors):${NC}"
heroku logs --tail -n 20 -a $APP_NAME | grep -E "(error|Error|ERROR|crashed)" || echo -e "${GREEN}No errors found in recent logs${NC}"

# 9. Get app info
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "\n${YELLOW}App Information:${NC}"
echo "URL: https://$APP_NAME.herokuapp.com"
echo "RTMS Dashboard: https://$APP_NAME.herokuapp.com/rtms"
echo "API Docs: https://$APP_NAME.herokuapp.com/api/docs"

# 10. Show Redis info
REDIS_URL=$(heroku config:get REDIS_URL -a $APP_NAME)
if [ ! -z "$REDIS_URL" ]; then
    echo -e "\n${YELLOW}Redis Status:${NC}"
    heroku redis:info -a $APP_NAME
fi

# 11. Cost warning
echo -e "\n${YELLOW}⚠️  Cost Information:${NC}"
echo "You are now running:"
echo "  - 1 web dyno"
echo "  - 1 RTMS service dyno"
echo "  - 1 worker (analytics) dyno"
echo "  - Redis Mini addon"
echo ""
echo "Estimated monthly cost:"
echo "  - Eco dynos: $5/month each = $15/month"
echo "  - Redis Mini: Free (first 1000 connections)"
echo "  - Total: ~$15/month"

echo -e "\n${GREEN}✅ All analytics features are now active!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Open https://$APP_NAME.herokuapp.com/rtms"
echo "2. Start a stream to test talk time analytics"
echo "3. Monitor with: heroku logs --tail -a $APP_NAME"
echo "4. Check analytics: heroku logs --tail --dyno=worker -a $APP_NAME"
