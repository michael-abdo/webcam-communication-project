#!/bin/bash

# Phase 2 API Testing Script for Heroku Deployment

BASE_URL="https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com"
TOKEN="test-heroku-api-key"

echo "=== Phase 2 Heroku API Testing Script ==="
echo "Base URL: $BASE_URL"
echo "API Token: $TOKEN"
echo "========================================"
echo

# Test 1: Create a session
echo "Test 1: Creating a new session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Heroku Phase 2 Test Session",
    "session_type": "interview",
    "metadata": {"test": "heroku_phase2", "deployment": "production"}
  }')

echo "Response: $SESSION_RESPONSE"
SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Session ID: $SESSION_ID"
echo

# Test 2: Register Zoom meeting with capture credentials
echo "Test 2: Registering Zoom meeting with capture credentials..."
ZOOM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "meeting_uuid": "zoom-test-'$(date +%s)'",
    "topic": "Heroku Test Meeting",
    "host_id": "heroku-host-123",
    "vault_credential_ref": "vault://credentials/heroku-test",
    "capture_worker_id": "worker-heroku-001"
  }')

echo "Response: $ZOOM_RESPONSE"
ZOOM_ID=$(echo "$ZOOM_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Zoom Meeting ID: $ZOOM_ID"
echo

# Test 3: Send capture worker heartbeat
echo "Test 3: Sending capture worker heartbeat..."
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

# Test 4: Create a participant
echo "Test 4: Creating a participant..."
PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "external_id": "heroku-participant-001",
    "name": "Heroku Test User",
    "role": "interviewee"
  }')

echo "Response: $PARTICIPANT_RESPONSE"
PARTICIPANT_ID=$(echo "$PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Participant ID: $PARTICIPANT_ID"
echo

# Test 5: Record participant event
echo "Test 5: Recording participant event (joined)..."
EVENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/zoom-participants/$PARTICIPANT_ID/events" \
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

# Test 6: Add transcript segment
echo "Test 6: Adding transcript segment..."
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

# Test 7: Get rolling transcript
echo "Test 7: Getting rolling transcript..."
ROLLING_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/transcript?since_segment=0" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $ROLLING_RESPONSE"
echo

# Test 8: Add analytics
echo "Test 8: Adding analytics metrics..."
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

# Test 9: Get per-participant analytics
echo "Test 9: Getting per-participant analytics..."
PARTICIPANT_ANALYTICS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $PARTICIPANT_ANALYTICS"
echo

# Test 10: Test WebSocket endpoint info
echo "Test 10: Testing WebSocket endpoint (info only)..."
WS_URL="wss://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/ws/sessions/$SESSION_ID"
echo "WebSocket URL would be: $WS_URL"
echo "(WebSocket testing requires a WebSocket client)"
echo

# Test 11: End session
echo "Test 11: Ending session..."
END_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/sessions/$SESSION_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "completed"}')

echo "Response: $END_RESPONSE"
echo

# Test 12: Verify all endpoints
echo "Test 12: Listing all sessions to verify..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $LIST_RESPONSE"
echo

echo "========================================"
echo "Phase 2 Heroku API Testing Complete!"
echo "========================================"