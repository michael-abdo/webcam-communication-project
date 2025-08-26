#!/bin/bash
# Quick deployment test script

URL="https://webcam-communication-project-production.up.railway.app"

echo "🧪 Testing your Railway deployment..."
echo "URL: $URL"
echo ""

# Test health endpoint
echo "1️⃣ Testing health endpoint..."
curl -s "$URL/health" | jq . || echo "❌ Health check failed"
echo ""

# Test info endpoint
echo "2️⃣ Testing info endpoint..."
curl -s "$URL/api/info" | jq . || echo "❌ Info endpoint failed"
echo ""

# Test metrics endpoint
echo "3️⃣ Testing metrics endpoint..."
curl -s "$URL/api/metrics" | jq . || echo "❌ Metrics endpoint failed"
echo ""

# Test analysis endpoint
echo "4️⃣ Testing fatigue analysis..."
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"perclos": 0.25, "confidence": 0.95}' \
  "$URL/api/analyze" | jq . || echo "❌ Analysis endpoint failed"
echo ""

echo "✅ Test complete!"