#!/bin/bash

# Corrected Phase 2 API Testing Script for Heroku

BASE_URL="https://xcellerate-eq-4f2dd61b4bbd.herokuapp.com"
TOKEN="test-heroku-api-key"

echo "=== Corrected Phase 2 API Testing on Heroku ==="
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

MEETING_ID=$(echo "$ZOOM_CREATE_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created Zoom meeting: $MEETING_ID"
echo

# Step 3: Register participant
echo "3. Registering participant..."
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

# Step 4: Create Zoom participant
echo "4. Creating Zoom participant..."
ZOOM_PARTICIPANT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/meetings/$MEETING_ID/participants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "participant_uuid": "zoom-participant-'$(date +%s)'",
    "participant_id": "'$PARTICIPANT_ID'",
    "user_name": "Test User",
    "zoom_user_id": "test-zoom-user-123",
    "join_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

ZOOM_PARTICIPANT_ID=$(echo "$ZOOM_PARTICIPANT_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✓ Created Zoom participant: $ZOOM_PARTICIPANT_ID"
echo

# Step 5: Record participant event (CORRECTED URL)
echo "5. Recording participant event..."
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

if [[ "$EVENT_RESPONSE" == *"error"* ]]; then
    echo "❌ Event recording failed: $EVENT_RESPONSE"
else
    echo "✓ Recorded event successfully"
fi
echo

# Step 6: Upload transcript (CORRECTED URL - no 's')
echo "6. Testing transcript upload endpoint..."
# First, let's check if the POST endpoint exists
TRANSCRIPT_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/sessions/$SESSION_ID/transcript" \
  -H "Authorization: Bearer $TOKEN" \
  -F "media=@/dev/null" \
  -F 'metadata={"status":"processing"}')
  
echo "Transcript upload endpoint returned: $TRANSCRIPT_TEST"
echo

# Step 7: Get rolling transcript (CORRECTED URL - no 's')
echo "7. Getting rolling transcript..."
ROLLING_TRANSCRIPT=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/transcript?since_segment=0" \
  -H "Authorization: Bearer $TOKEN")

echo "Rolling transcript: $ROLLING_TRANSCRIPT"
echo

# Step 8: Add transcription segment via RTMS
echo "8. Adding transcription segment via RTMS..."
SEGMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/rtms/transcription/segments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "participant_id": "'$PARTICIPANT_ID'",
    "text": "This is a test transcript from corrected Heroku test.",
    "start_time": 0.0,
    "end_time": 5.0,
    "confidence": 0.95,
    "language": "en"
  }')

echo "Segment response: $(echo "$SEGMENT_RESPONSE" | head -c 100)..."
echo

# Step 9: Create analytics (CORRECTED URL)
echo "9. Creating analytics via correct endpoint..."
ANALYTICS_CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/analytics/compute/$MEETING_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "total_duration_seconds": 300,
    "participant_count": 1,
    "talk_time_distribution": {
      "'$PARTICIPANT_ID'": 45.5
    },
    "interruption_count": 2,
    "avg_speech_pace": 150
  }')

echo "Analytics response: $(echo "$ANALYTICS_CREATE_RESPONSE" | head -c 100)..."
echo

# Step 10: Get session analytics
echo "10. Getting session analytics..."
SESSION_ANALYTICS=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/analytics" \
  -H "Authorization: Bearer $TOKEN")

echo "Session analytics: $(echo "$SESSION_ANALYTICS" | head -c 200)..."
echo

# Step 11: Test WebSocket endpoint
echo "11. WebSocket endpoint..."
WS_URL="wss://xcellerate-eq-4f2dd61b4bbd.herokuapp.com/ws/sessions/$SESSION_ID"
echo "WebSocket URL: $WS_URL"
echo

# Step 12: Get session events (if endpoint exists)
echo "12. Testing session events endpoint..."
EVENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/sessions/$SESSION_ID/events" \
  -H "Authorization: Bearer $TOKEN")

if [[ "$EVENTS_RESPONSE" == *"Endpoint not found"* ]]; then
    echo "Session events endpoint not implemented yet"
else
    echo "Session events: $(echo "$EVENTS_RESPONSE" | head -c 100)..."
fi
echo

echo "=============================================="
echo "✓ Corrected Phase 2 API Testing Complete!"
echo "=============================================="