# Event Router Setup and Usage Guide

## Overview

The Event Router is a Redis-based pub/sub system that streams real-time events from the RTMS service to analytics microservices. It enables scalable, decoupled analytics processing without impacting the main application's performance.

## Architecture

```
┌─────────────┐       ┌─────────────┐       ┌──────────────────┐
│    RTMS     │       │    Redis    │       │    Analytics     │
│   Service   │──────▶│   Pub/Sub   │──────▶│   Services       │
│             │       │   Channels   │       │                  │
└─────────────┘       └─────────────┘       └──────────────────┘
      │                                              │
      │                                              ▼
      │                                      ┌──────────────────┐
      │                                      │   Time-Series    │
      └─────────────────────────────────────▶│    Database      │
                 S3 Event Store               └──────────────────┘
```

## Event Types and Channels

### Available Event Channels

1. **`analytics:audio`** - Audio chunk events
   ```json
   {
     "eventId": "uuid",
     "eventType": "audio",
     "sessionId": "session_id",
     "timestamp": 1234567890,
     "data": {
       "participantId": "participant_uuid",
       "userId": "zoom_user_id",
       "userName": "John Doe",
       "duration": 160,  // milliseconds
       "s3Key": "audio/session/chunk.pcm16",
       "sampleRate": 16000,
       "channels": 1,
       "sequenceNo": 123
     }
   }
   ```

2. **`analytics:transcript`** - Transcript segment events
   ```json
   {
     "eventId": "uuid",
     "eventType": "transcript",
     "sessionId": "session_id",
     "timestamp": 1234567890,
     "data": {
       "participantId": "participant_uuid",
       "userId": "zoom_user_id",
       "userName": "John Doe",
       "text": "Hello everyone",
       "startTime": 10.5,  // seconds
       "endTime": 12.3,
       "confidence": 0.95,
       "language": "en"
     }
   }
   ```

3. **`analytics:video`** - Video frame events
   ```json
   {
     "eventId": "uuid",
     "eventType": "video",
     "sessionId": "session_id",
     "timestamp": 1234567890,
     "data": {
       "participantId": "participant_uuid",
       "frameId": "uuid",
       "s3Key": "video/session/frame.jpg",
       "resolution": {"width": 640, "height": 480},
       "sequenceNo": 456
     }
   }
   ```

4. **`analytics:session`** - Session lifecycle events
   ```json
   {
     "eventId": "uuid",
     "eventType": "session",
     "sessionId": "session_id",
     "timestamp": 1234567890,
     "data": {
       "action": "start|end",
       "meetingId": "meeting_uuid",
       "participantCount": 5,
       "duration": 3600  // seconds (for end events)
     }
   }
   ```

5. **`analytics:participant`** - Participant events
   ```json
   {
     "eventId": "uuid",
     "eventType": "participant",
     "sessionId": "session_id",
     "timestamp": 1234567890,
     "data": {
       "action": "join|leave|mute|unmute",
       "participantId": "participant_uuid",
       "userId": "zoom_user_id",
       "userName": "John Doe"
     }
   }
   ```

## Setup Instructions

### 1. Start Redis with Docker Compose

```bash
cd /home/Mike/projects/Xenodex/greg/phase-2
docker-compose up -d redis
```

### 2. Configure Environment Variables

```bash
# For RTMS Service
export REDIS_URL=redis://localhost:6379
export S3_BUCKET=your-s3-bucket
export EVENT_STORE_BUCKET=your-event-store-bucket  # Optional

# For Analytics Services
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=postgresql://user:pass@localhost/xenodex_analytics
```

### 3. Set Up Analytics Database

```bash
cd analytics_services
python setup_database.py
```

### 4. Start Analytics Services

```bash
# Talk Time Analytics
python analytics_services/talk_time_analytics.py

# Add more services as needed
# python analytics_services/interruption_analytics.py
# python analytics_services/engagement_analytics.py
```

### 5. Start RTMS Service

```bash
cd rtms-service
npm install
npm start
```

## Creating New Analytics Services

### 1. Copy the Template

```bash
cp analytics_services/service_template.py analytics_services/my_new_analytics.py
```

### 2. Implement Your Service

```python
from base_analytics_service import BaseAnalyticsService, run_service

class MyNewAnalyticsService(BaseAnalyticsService):
    def __init__(self, **kwargs):
        super().__init__(service_name="my_new_analytics", **kwargs)
    
    def get_event_types(self):
        # Subscribe to the events you need
        return ["audio", "transcript"]
    
    async def process_event(self, event, event_type):
        # Process events and calculate metrics
        session_id = event["sessionId"]
        data = event["data"]
        
        # Your analytics logic here
        metric_value = calculate_something(data)
        
        # Publish metrics
        await self.publish_metric(
            "my_metric_name",
            metric_value,
            session_id,
            participant_id=data.get("participantId")
        )

if __name__ == "__main__":
    run_service(MyNewAnalyticsService)
```

### 3. Deploy Your Service

```bash
# Local development
python analytics_services/my_new_analytics.py

# Production (using systemd)
sudo cp analytics_services/systemd/my_new_analytics.service /etc/systemd/system/
sudo systemctl enable my_new_analytics
sudo systemctl start my_new_analytics
```

## Testing

### 1. Run Integration Tests

```bash
python analytics_services/test_integration.py
```

### 2. Test with Simulated Events

```bash
# Start analytics services first
python analytics_services/talk_time_analytics.py &

# Run test publisher
node test_event_publisher.js test-session-123 30
```

### 3. Monitor Redis Channels

```bash
# Check active channels
redis-cli PUBSUB CHANNELS

# Monitor specific channel
redis-cli SUBSCRIBE analytics:transcript

# Check subscriber count
redis-cli PUBSUB NUMSUB analytics:audio analytics:transcript
```

## Production Deployment

### Redis Configuration

For production, use Redis with:
- Persistence enabled (AOF)
- Replication for high availability
- SSL/TLS encryption
- Password authentication

### Heroku Redis

```bash
# Add Redis to your Heroku app
heroku addons:create heroku-redis:mini -a your-app-name

# Get connection URL
heroku config:get REDIS_URL -a your-app-name
```

### AWS ElastiCache

```bash
# Use ElastiCache for Redis with:
# - Multi-AZ deployment
# - Automatic failover
# - Encryption at rest and in transit
```

## Monitoring

### Key Metrics to Track

1. **Event Publishing Rate**
   - Events per second by type
   - Failed publish attempts
   - Event size distribution

2. **Analytics Processing**
   - Processing latency per service
   - Metrics generated per minute
   - Error rates by service

3. **Redis Performance**
   - Pub/sub channel activity
   - Memory usage
   - Connected clients
   - Command latency

### Monitoring Commands

```bash
# Redis metrics
redis-cli INFO stats
redis-cli CLIENT LIST
redis-cli PUBSUB CHANNELS

# Service health check
curl http://localhost:8080/health  # RTMS service
curl http://localhost:9090/metrics  # Analytics service metrics
```

## Troubleshooting

### Common Issues

1. **Events not being received**
   - Check Redis connection: `redis-cli PING`
   - Verify channel names match
   - Check service subscriptions: `redis-cli PUBSUB CHANNELS`

2. **High latency**
   - Monitor Redis memory: `redis-cli INFO memory`
   - Check network latency to Redis
   - Review analytics service processing time

3. **Missing events**
   - Check S3 event store for failed events
   - Review RTMS service logs
   - Verify event publisher error handling

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run service with verbose output
python analytics_services/talk_time_analytics.py --debug
```

## Best Practices

1. **Event Design**
   - Keep events small and focused
   - Include all necessary context in each event
   - Use consistent field names across event types

2. **Service Design**
   - One metric type per service
   - Process events asynchronously
   - Batch database writes when possible
   - Implement graceful shutdown

3. **Error Handling**
   - Log but don't crash on bad events
   - Store failed events for replay
   - Monitor error rates
   - Implement circuit breakers for downstream services

4. **Performance**
   - Use Redis connection pooling
   - Implement event batching for high-volume streams
   - Consider event sampling for non-critical metrics
   - Use time-series database for metric storage

## API Reference

### BaseAnalyticsService Methods

```python
# Subscribe to event types
def get_event_types() -> List[str]

# Process incoming events
async def process_event(event: Dict[str, Any], event_type: str)

# Publish metrics
async def publish_metric(
    metric_name: str,
    value: float,
    session_id: str,
    participant_id: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None
)

# Increment counters
async def increment_counter(
    counter_name: str,
    session_id: str,
    participant_id: Optional[str] = None,
    increment: int = 1
) -> int

# Get cached values
async def get_cached_metric(
    metric_name: str,
    session_id: str,
    participant_id: Optional[str] = None
) -> Optional[float]
```

## Future Enhancements

1. **Event Schema Validation**
   - JSON Schema validation for all events
   - Automatic schema evolution tracking

2. **Advanced Analytics**
   - Real-time anomaly detection
   - ML-based engagement scoring
   - Predictive analytics

3. **Scalability**
   - Kafka integration for higher throughput
   - Event partitioning by session
   - Horizontal scaling of analytics services

4. **Observability**
   - OpenTelemetry integration
   - Distributed tracing
   - Custom dashboards
