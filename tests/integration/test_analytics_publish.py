#!/usr/bin/env python3
"""Test script to manually publish analytics event to Redis."""

import os
import json
import redis
from datetime import datetime, timezone

# Get Redis URL from environment
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
print(f"Connecting to Redis: {redis_url[:30]}...")

# Connect to Redis
r = redis.from_url(redis_url, decode_responses=True)

# Create test analytics event
test_event = {
    "service": "manual_test",
    "metric": "talk_time_seconds", 
    "value": 123.45,
    "session_id": "60340c86-3bd2-4150-b87d-671340b6ef97",
    "participant_id": "test-participant-001",
    "tags": {
        "user_name": "Test User",
        "user_id": "test-001"
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Publish to analytics:metrics channel
channel = "analytics:metrics"
event_json = json.dumps(test_event)
subscribers = r.publish(channel, event_json)

print(f"Published test event to '{channel}' channel")
print(f"Event: {event_json}")
print(f"Subscribers: {subscribers}")