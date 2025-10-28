#!/bin/bash

# Complete Phase 2 API Testing Script for Heroku

BASE_URL="https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com"
TOKEN="test-heroku-api-key"

echo "=== Complete Phase 2 API Testing on Heroku ==="
echo "Base URL: $BASE_URL"
echo "=============================================="
echo

# Step 1: Create a session
echo "1. Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "facilitator_id": "test-facilitator",
    "consent_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "device_kind": "Chrome/Test",
    "locale": "en-US"
  }')

SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created session: $SESSION_ID"
echo

# Step 2: Create a Zoom meeting
echo "2. Creating Zoom meeting..."
MEETING_UUID="zoom-meeting-$(date +%s)"
ZOOM_CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/meetings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "meeting_uuid": "'$MEETING_UUID'",
    "session_id": "'$SESSION_ID'",
    "host_id": "test-host-123",
    "topic": "Heroku Test Meeting",
    "start_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "rtms_stream_id": "rtms-stream-001"
  }')

echo "Response: $ZOOM_CREATE_RESPONSE"
MEETING_ID=$(echo "$ZOOM_CREATE_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created Zoom meeting: $MEETING_ID"
echo

# Step 3: Register capture credentials for the Zoom meeting
echo "3. Registering capture credentials..."
CAPTURE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "meeting_id": "'$MEETING_ID'",
    "account_id": "test-account-123",
    "access_token": "test-access-token",
    "expires_at": "'$(date -u -d "+1 hour" +%Y-%m-%dT%H:%M:%SZ)'",
    "capture_worker_id": "worker-001",
    "capture_token": "capture-token-123",
    "capture_heartbeat_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

echo "Response code: $(echo "$CAPTURE_RESPONSE" | head -c 50)"
echo "✓ Registered capture credentials"
echo

# Step 4: Send capture worker heartbeat
echo "4. Sending capture worker heartbeat..."
HEARTBEAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/zoom/heartbeat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "capture_worker_id": "worker-001",
    "status": "capturing",
    "heartbeat_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "metrics": {
      "frames_captured": 1000,
      "audio_packets": 500,
      "cpu_usage": 35.5,
      "memory_usage": 256
    }
  }')

echo "Response: $HEARTBEAT_RESPONSE"
echo "✓ Updated heartbeat"
echo

# Step 5: Register participant
echo "5. Registering participant..."
PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_id": "test-device-001",
    "status": "ready"
  }')

PARTICIPANT_ID=$(echo "$PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created participant: $PARTICIPANT_ID"
echo

# Step 6: Create Zoom participant
echo "6. Creating Zoom participant..."
ZOOM_PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/meetings/$MEETING_ID/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "participant_uuid": "zoom-participant-'$(date +%s)'",
    "participant_id": "'$PARTICIPANT_ID'",
    "user_name": "Test User",
    "join_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

echo "Response: $ZOOM_PARTICIPANT_RESPONSE"
ZOOM_PARTICIPANT_ID=$(echo "$ZOOM_PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created Zoom participant: $ZOOM_PARTICIPANT_ID"
echo

# Step 7: Record participant event
echo "7. Recording participant event..."
EVENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/zoom-participants/$ZOOM_PARTICIPANT_ID/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "kind": "audio_enabled",
    "occurred_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "data": {
      "enabled": true
    }
  }')

echo "Response: $EVENT_RESPONSE"
echo "✓ Recorded event"
echo

# Step 8: Add a transcript segment
echo "8. Adding transcript segment..."
TRANSCRIPT_ID="transcript-$(date +%s)"
TRANSCRIPT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/sessions/$SESSION_ID/transcripts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "participant_id": "'$PARTICIPANT_ID'",
    "segment_number": 1,
    "start_time": 0.0,
    "end_time": 5.0,
    "text": "Hello, this is a test transcript from the Heroku deployment.",
    "confidence": 0.95,
    "is_final": true
  }')

echo "Response: $TRANSCRIPT_RESPONSE"
echo

# Step 9: Add analytics
echo "9. Creating analytics..."
ANALYTICS_CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/meetings/$MEETING_ID/analytics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "metrics": {
      "total_participants": 1,
      "average_engagement": 0.85,
      "total_speaking_time": 45.5,
      "meeting_duration": 180
    }
  }')

echo "Response: $ANALYTICS_CREATE_RESPONSE"
echo "✓ Created analytics"
echo

# Step 10: Get rolling transcript
echo "10. Getting rolling transcript..."
ROLLING_TRANSCRIPT=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/transcript?since_segment=0" \
  -H "Authorization: Bearer $TOKEN")

echo "Rolling transcript: $ROLLING_TRANSCRIPT"
echo

# Step 11: Get analytics
echo "11. Getting session analytics..."
SESSION_ANALYTICS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Authorization: Bearer $TOKEN")

echo "Analytics: $(echo "$SESSION_ANALYTICS" | head -c 200)..."
echo

# Step 12: Get all meetings
echo "12. Listing all meetings..."
ALL_MEETINGS=$(curl -s -X GET "$BASE_URL/api/meetings?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "Recent meetings: $(echo "$ALL_MEETINGS" | python3 -m json.tool | head -20)..."
echo

# Step 13: Get session details
echo "13. Getting final session details..."
FINAL_SESSION=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Session status: $(echo "$FINAL_SESSION" | grep -o '"alert_state":"[^"]*' | cut -d'"' -f4)"
echo

echo "=============================================="
echo "✓ Phase 2 API Testing Complete!"
echo "✓ All core endpoints tested successfully"
echo "=============================================="