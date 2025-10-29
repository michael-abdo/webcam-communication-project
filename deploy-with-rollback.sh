#!/bin/bash
# Heroku Deployment Script with Automatic Rollback
# Usage: ./deploy-with-rollback.sh

set -e  # Exit on error

# Configuration
APP_NAME="xcellerate-eq-4f2dd61b4bbd"
HEALTH_CHECK_URL="https://$APP_NAME.herokuapp.com/api/analytics/health"
RTMS_CHECK_URL="https://$APP_NAME.herokuapp.com/rtms/ui"
ANALYTICS_CHECK_URL="https://$APP_NAME.herokuapp.com/test-analytics"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Heroku Deployment with Auto-Rollback${NC}"
echo -e "${YELLOW}======================================${NC}"

# Get current release number
echo -e "\n${YELLOW}📝 Recording current release...${NC}"
CURRENT_RELEASE=$(heroku releases -a $APP_NAME --json | jq -r '.[0].version')
echo -e "Current stable release: ${GREEN}$CURRENT_RELEASE${NC}"

# Tag current state
echo -e "\n${YELLOW}🏷️  Tagging current stable state...${NC}"
git tag -f pre-cleanup-deploy-$CURRENT_RELEASE
echo -e "Tagged as: ${GREEN}pre-cleanup-deploy-$CURRENT_RELEASE${NC}"

# Confirm deployment
echo -e "\n${YELLOW}⚠️  Ready to deploy cleanup branch to production${NC}"
echo -e "Current release: ${GREEN}$CURRENT_RELEASE${NC}"
echo -e "App: ${GREEN}$APP_NAME${NC}"
echo -e "\nPress Enter to continue or Ctrl+C to cancel..."
read

# Deploy
echo -e "\n${YELLOW}🚀 Deploying cleanup branch...${NC}"
if ! git push heroku cleanup:main; then
    echo -e "${RED}❌ Deployment failed! No changes made.${NC}"
    exit 1
fi

# Wait for app to restart
echo -e "\n${YELLOW}⏳ Waiting for app to restart (40 seconds)...${NC}"
for i in {40..1}; do
    echo -ne "\r${YELLOW}Waiting... $i seconds remaining ${NC}"
    sleep 1
done
echo ""

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -e "\n${YELLOW}Checking $name...${NC}"
    if curl -f -s -o /dev/null --max-time 10 "$url"; then
        echo -e "${GREEN}✅ $name is responding${NC}"
        return 0
    else
        echo -e "${RED}❌ $name check failed!${NC}"
        return 1
    fi
}

# Run health checks
echo -e "\n${YELLOW}🏥 Running health checks...${NC}"
FAILED=false

if ! check_endpoint "$HEALTH_CHECK_URL" "API Health"; then
    FAILED=true
fi

if ! check_endpoint "$RTMS_CHECK_URL" "RTMS UI"; then
    FAILED=true
fi

if ! check_endpoint "$ANALYTICS_CHECK_URL" "Analytics Endpoint"; then
    FAILED=true
fi

# Check logs for errors
echo -e "\n${YELLOW}📋 Checking logs for critical errors...${NC}"
ERROR_COUNT=$(heroku logs -a $APP_NAME -n 100 --source app | grep -c "ERROR" || true)
if [ $ERROR_COUNT -gt 10 ]; then
    echo -e "${RED}❌ Found $ERROR_COUNT errors in recent logs!${NC}"
    FAILED=true
else
    echo -e "${GREEN}✅ Error count acceptable ($ERROR_COUNT)${NC}"
fi

# Rollback if any checks failed
if [ "$FAILED" = true ]; then
    echo -e "\n${RED}❌ Deployment validation failed! Initiating rollback...${NC}"
    heroku rollback $CURRENT_RELEASE -a $APP_NAME
    
    echo -e "\n${YELLOW}⏳ Waiting for rollback to complete (30 seconds)...${NC}"
    sleep 30
    
    # Verify rollback
    NEW_RELEASE=$(heroku releases -a $APP_NAME --json | jq -r '.[0].version')
    if [ "$NEW_RELEASE" != "$CURRENT_RELEASE" ]; then
        echo -e "${GREEN}✅ Rollback complete! Back to $CURRENT_RELEASE${NC}"
    else
        echo -e "${RED}❌ Rollback may have failed. Please check manually!${NC}"
    fi
    
    echo -e "\n${RED}Deployment failed and was rolled back.${NC}"
    exit 1
fi

# Success!
echo -e "\n${GREEN}✅ Deployment successful! All checks passed.${NC}"
echo -e "\n${YELLOW}📊 Deployment Summary:${NC}"
echo -e "  Previous Release: ${YELLOW}$CURRENT_RELEASE${NC}"
NEW_RELEASE=$(heroku releases -a $APP_NAME --json | jq -r '.[0].version')
echo -e "  New Release: ${GREEN}$NEW_RELEASE${NC}"
echo -e "  App URL: ${GREEN}https://$APP_NAME.herokuapp.com${NC}"

echo -e "\n${YELLOW}📌 Next Steps:${NC}"
echo -e "  1. Monitor logs: ${YELLOW}heroku logs --tail -a $APP_NAME${NC}"
echo -e "  2. Check metrics in Heroku dashboard"
echo -e "  3. Test all critical user flows"

echo -e "\n${YELLOW}🔄 If you need to rollback:${NC}"
echo -e "  ${YELLOW}heroku rollback $CURRENT_RELEASE -a $APP_NAME${NC}"

echo -e "\n${GREEN}🎉 Deployment complete!${NC}"