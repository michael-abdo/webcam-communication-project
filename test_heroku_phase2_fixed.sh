#!/bin/bash

# Phase 2 API Testing Script for Heroku Deployment (Fixed)

BASE_URL="https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com"
TOKEN="test-heroku-api-key"

echo "=== Phase 2 Heroku API Testing Script (Fixed) ==="
echo "Base URL: $BASE_URL"
echo "API Token: $TOKEN"
echo "============================================="
echo

# Test 1: Create a session with required fields
echo "Test 1: Creating a new session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "facilitator_id": "heroku-facilitator-001",
    "consent_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "device_kind": "Chrome/Heroku Test",
    "locale": "en-US"
  }')

echo "Response: $SESSION_RESPONSE"
SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Session ID: $SESSION_ID"
echo

# Test 2: Register participant (Phase 1 style)
echo "Test 2: Registering participant..."
PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_id": "heroku-device-001",
    "status": "awaiting-consent"
  }')

echo "Response: $PARTICIPANT_RESPONSE"
PARTICIPANT_ID=$(echo "$PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Participant ID: $PARTICIPANT_ID"
echo

# Test 3: Register Zoom meeting with capture credentials (Phase 2)
echo "Test 3: Registering Zoom meeting with capture credentials..."
ZOOM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "meeting_uuid": "zoom-heroku-'$(date +%s)'",
    "topic": "Heroku Test Meeting",
    "host_id": "heroku-host-123",
    "vault_credential_ref": "vault://credentials/heroku-test",
    "capture_worker_id": "worker-heroku-001"
  }')

echo "Response: $ZOOM_RESPONSE"
ZOOM_ID=$(echo "$ZOOM_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Zoom Meeting ID: $ZOOM_ID"
echo

# Test 4: Send capture worker heartbeat
echo "Test 4: Sending capture worker heartbeat..."
HEARTBEAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom/heartbeat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "capture_worker_id": "worker-heroku-001",
    "status": "capturing",
    "metrics": {
      "frames_captured": 1200,
      "audio_packets": 800,
      "cpu_usage": 45.5,
      "memory_usage": 512
    }
  }')

echo "Response: $HEARTBEAT_RESPONSE"
echo

# Test 5: Create a participant via Phase 2 endpoint
echo "Test 5: Creating a participant (Phase 2 style)..."
PARTICIPANT2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "external_id": "heroku-participant-002",
    "name": "Heroku Test User 2",
    "role": "interviewee"
  }')

echo "Response: $PARTICIPANT2_RESPONSE"
PARTICIPANT2_ID=$(echo "$PARTICIPANT2_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Participant 2 ID: $PARTICIPANT2_ID"
echo

# Test 6: Record participant event
echo "Test 6: Recording participant event (joined)..."
# Use the second participant ID if available, otherwise use first
TEST_PARTICIPANT_ID=${PARTICIPANT2_ID:-$PARTICIPANT_ID}
EVENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/zoom-participants/$TEST_PARTICIPANT_ID/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "event_type": "joined",
    "event_data": {
      "audio_enabled": true,
      "video_enabled": true,
      "join_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }
  }')

echo "Response: $EVENT_RESPONSE"
echo

# Test 7: Add transcript segment
echo "Test 7: Adding transcript segment..."
TRANSCRIPT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/transcripts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "participant_id": "'$PARTICIPANT_ID'",
    "segment_number": 1,
    "start_time": 0.0,
    "end_time": 5.5,
    "text": "Hello, this is a test transcript from Heroku deployment.",
    "confidence": 0.95,
    "is_final": true
  }')

echo "Response: $TRANSCRIPT_RESPONSE"
echo

# Test 8: Get rolling transcript
echo "Test 8: Getting rolling transcript..."
ROLLING_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/transcript?since_segment=0" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $ROLLING_RESPONSE"
echo

# Test 9: Add analytics
echo "Test 9: Adding analytics metrics..."
ANALYTICS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "participant_id": "'$PARTICIPANT_ID'",
    "metrics": {
      "speaking_time": 45.5,
      "interruptions": 2,
      "sentiment_score": 0.75,
      "energy_level": 0.8,
      "engagement_score": 0.85
    },
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

echo "Response: $ANALYTICS_RESPONSE"
echo

# Test 10: Get per-participant analytics
echo "Test 10: Getting per-participant analytics..."
PARTICIPANT_ANALYTICS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $PARTICIPANT_ANALYTICS"
echo

# Test 11: Get session events
echo "Test 11: Getting session events..."
SESSION_EVENTS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/events" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $SESSION_EVENTS"
echo

# Test 12: End session
echo "Test 12: Ending session..."
END_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/sessions/$SESSION_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "completed"}')

echo "Response: $END_RESPONSE"
echo

# Test 13: Get session details
echo "Test 13: Getting session details..."
SESSION_DETAILS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $SESSION_DETAILS"
echo

# Test 14: Test WebSocket info
echo "Test 14: WebSocket endpoint info..."
WS_URL="wss://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/ws/sessions/$SESSION_ID"
echo "WebSocket URL: $WS_URL"
echo "(WebSocket testing requires a WebSocket client)"
echo

echo "============================================="
echo "Phase 2 Heroku API Testing Complete!"
echo "============================================="