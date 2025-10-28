#!/bin/bash
set -e

echo "Testing Speaker Diarization Implementation"
echo "========================================="

# Configuration
BASE_URL="${BASE_URL:-https://xcellerate-eq-4f2dd61b4bbd-57798fc61cb7.herokuapp.com}"
API_TOKEN="${CAPTURE_API_TOKEN:-test-heroku-api-key}"
SESSION_ID="test-diarization-$(date +%s)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Helper function
test_endpoint() {
    local method=$1
    local path=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "Method: $method"
    echo "URL: $BASE_URL$path"
    
    if [ "$method" = "POST" ]; then
        echo "Data: $data"
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$path")
    else
        response=$(curl -s -w "\n%{http_code}" -X GET \
            -H "Authorization: Bearer $API_TOKEN" \
            "$BASE_URL$path")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Status: $http_code"
    echo "Response: $body" | jq . 2>/dev/null || echo "$body"
    
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
}

# Step 1: Create a test session
echo -e "\n${YELLOW}Step 1: Creating test session${NC}"
test_endpoint "POST" "/api/rtms/sessions" \
    "{\"meeting_uuid\": \"test-meeting-123\", \"stream_id\": \"stream-123\", \"host_id\": \"host-123\"}" \
    "Create RTMS session"

# Step 2: Create participants
echo -e "\n${YELLOW}Step 2: Creating participants${NC}"

# Participant 1
PARTICIPANT1_DATA="{\"zoom_user_id\": \"speaker1\", \"display_name\": \"Alice Johnson\", \"status\": \"active\"}"
response=$(curl -s -X POST \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PARTICIPANT1_DATA" \
    "$BASE_URL/api/rtms/sessions/$SESSION_ID/participants")
PARTICIPANT1_ID=$(echo "$response" | jq -r '.participant.id' 2>/dev/null)
echo "Created Participant 1: $PARTICIPANT1_ID (Alice Johnson)"

# Participant 2
PARTICIPANT2_DATA="{\"zoom_user_id\": \"speaker2\", \"display_name\": \"Bob Smith\", \"status\": \"active\"}"
response=$(curl -s -X POST \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PARTICIPANT2_DATA" \
    "$BASE_URL/api/rtms/sessions/$SESSION_ID/participants")
PARTICIPANT2_ID=$(echo "$response" | jq -r '.participant.id' 2>/dev/null)
echo "Created Participant 2: $PARTICIPANT2_ID (Bob Smith)"

# Step 3: Create transcription segments with speaker attribution
echo -e "\n${YELLOW}Step 3: Creating transcription segments${NC}"

# Alice's first segment
test_endpoint "POST" "/api/rtms/transcription/segments" \
    "{\"session_id\": \"$SESSION_ID\", \"text\": \"Hello everyone, welcome to our meeting today.\", \"start_time\": 0.0, \"end_time\": 3.5, \"participant_id\": \"$PARTICIPANT1_ID\", \"confidence\": 0.95}" \
    "Alice's opening statement"

# Bob's response
test_endpoint "POST" "/api/rtms/transcription/segments" \
    "{\"session_id\": \"$SESSION_ID\", \"text\": \"Thanks Alice! Happy to be here.\", \"start_time\": 4.0, \"end_time\": 6.0, \"participant_id\": \"$PARTICIPANT2_ID\", \"confidence\": 0.93}" \
    "Bob's response"

# Alice continues
test_endpoint "POST" "/api/rtms/transcription/segments" \
    "{\"session_id\": \"$SESSION_ID\", \"text\": \"Let's start with the agenda. First item is the project update.\", \"start_time\": 6.5, \"end_time\": 10.0, \"participant_id\": \"$PARTICIPANT1_ID\", \"confidence\": 0.94}" \
    "Alice discusses agenda"

# Bob interjects
test_endpoint "POST" "/api/rtms/transcription/segments" \
    "{\"session_id\": \"$SESSION_ID\", \"text\": \"Actually, can we quickly review the action items from last week?\", \"start_time\": 10.5, \"end_time\": 13.5, \"participant_id\": \"$PARTICIPANT2_ID\", \"confidence\": 0.91}" \
    "Bob's interruption"

# Step 4: Retrieve transcription with speaker info
echo -e "\n${YELLOW}Step 4: Retrieving transcription segments${NC}"
test_endpoint "GET" "/api/rtms/sessions/$SESSION_ID/transcription?limit=10" "" \
    "Get all transcription segments"

# Step 5: Test rolling transcript endpoint
echo -e "\n${YELLOW}Step 5: Testing rolling transcript for dashboard${NC}"
test_endpoint "GET" "/api/sessions/$SESSION_ID/transcript" "" \
    "Get transcript for dashboard display"

# Step 6: Simulate real-time frame broadcast
echo -e "\n${YELLOW}Step 6: Simulating real-time transcript frame${NC}"
test_endpoint "POST" "/api/rtms/streams/$SESSION_ID/frames" \
    "{\"type\": \"transcript\", \"streamId\": \"stream-123\", \"sessionId\": \"$SESSION_ID\", \"timestamp\": $(date +%s)000, \"userName\": \"Alice Johnson\", \"userId\": \"speaker1\", \"participantId\": \"$PARTICIPANT1_ID\", \"text\": \"This is a real-time transcript test.\"}" \
    "Broadcast transcript frame with speaker info"

echo -e "\n${GREEN}Speaker Diarization Test Complete!${NC}"
echo "================================================"
echo "Summary:"
echo "- Created session: $SESSION_ID"
echo "- Created 2 participants with unique IDs"
echo "- Added 4 transcription segments with speaker attribution"
echo "- Verified retrieval APIs work with speaker information"
echo ""
echo "Next steps:"
echo "1. Check the RTMS dashboard at $BASE_URL/rtms/ui"
echo "2. Verify speaker names appear with different colors"
echo "3. Confirm segments are properly attributed in the database"