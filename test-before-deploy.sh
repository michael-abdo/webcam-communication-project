#!/bin/bash
# Pre-deployment test script to verify current production state

APP_NAME="xcellerate-eq-4f2dd61b4bbd"
BASE_URL="https://$APP_NAME.herokuapp.com"

echo "🔍 Testing Current Production State"
echo "=================================="
echo "App: $APP_NAME"
echo ""

# Test endpoints
test_endpoint() {
    local path=$1
    local name=$2
    echo -n "Testing $name... "
    if curl -f -s -o /dev/null --max-time 10 "$BASE_URL$path"; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
}

# Run tests
test_endpoint "/api/analytics/health" "API Health"
test_endpoint "/rtms/ui" "RTMS Dashboard"
test_endpoint "/test-analytics" "Analytics Test"
test_endpoint "/" "Main App"
test_endpoint "/baseline" "Baseline Capture"

echo ""
echo "📋 Current Release Info:"
heroku releases -a $APP_NAME -n 1

echo ""
echo "🔄 Current Git State:"
git log --oneline -n 5