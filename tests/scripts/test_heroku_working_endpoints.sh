#!/bin/bash

# Testing Working Phase 2 Endpoints on Heroku

BASE_URL="https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com"
TOKEN="test-heroku-api-key"

echo "=== Testing Working Phase 2 Endpoints ==="
echo

# Create a session
echo "1. Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "facilitator_id": "test-facilitator",
    "consent_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "device_kind": "Chrome Test",
    "locale": "en-US"
  }')

SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Created session: $SESSION_ID"
echo

# Register participant
echo "2. Registering participant..."
PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_id": "test-device-001",
    "status": "awaiting-consent"
  }')

PARTICIPANT_ID=$(echo "$PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Created participant: $PARTICIPANT_ID"
echo

# Test Zoom registration with corrected parameters
echo "3. Registering Zoom meeting (with meeting_id)..."
ZOOM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "meeting_id": "zoom-'$(date +%s)'",
    "meeting_uuid": "zoom-uuid-'$(date +%s)'",
    "topic": "Test Meeting",
    "host_id": "host-123",
    "vault_credential_ref": "vault://credentials/test",
    "capture_worker_id": "worker-001"
  }')

echo "Response: $ZOOM_RESPONSE"
ZOOM_ID=$(echo "$ZOOM_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo

# Test heartbeat with corrected parameters
echo "4. Sending heartbeat (with heartbeat_at)..."
HEARTBEAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom/heartbeat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "capture_worker_id": "worker-001",
    "status": "capturing",
    "heartbeat_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "metrics": {
      "frames_captured": 100,
      "cpu_usage": 25.5
    }
  }')

echo "Response: $HEARTBEAT_RESPONSE"
echo

# Test participant event with corrected parameters
echo "5. Recording participant event (with kind)..."
EVENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/zoom-participants/$PARTICIPANT_ID/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "kind": "joined",
    "event_type": "joined",
    "event_data": {
      "audio_enabled": true,
      "video_enabled": true
    }
  }')

echo "Response: $EVENT_RESPONSE"
echo

# Get rolling transcript
echo "6. Getting rolling transcript..."
TRANSCRIPT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/transcript?since_segment=0" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $TRANSCRIPT_RESPONSE"
echo

# Try to get analytics (should work after zoom meeting is registered)
echo "7. Getting analytics..."
ANALYTICS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $ANALYTICS_RESPONSE"
echo

# Get session details
echo "8. Getting session details..."
SESSION_DETAILS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Response (truncated): $(echo "$SESSION_DETAILS" | head -c 200)..."
echo

echo "=== Test Complete ==="