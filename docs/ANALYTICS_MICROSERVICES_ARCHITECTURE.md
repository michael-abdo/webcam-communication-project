# Analytics Microservices Architecture

## Overview

This architecture enables infinite analytics microservices to be added without impacting core system latency by using event-driven, asynchronous processing with a CQRS pattern.

## Core Principles

1. **Zero Latency Impact**: Analytics never block the main data flow
2. **Infinite Scalability**: Add services without architectural changes
3. **Real-time & Batch**: Support both processing modes
4. **Failure Isolation**: One service failure doesn't affect others
5. **Replay Capability**: Reprocess historical data for new analytics

## Architecture Diagram

```
┌─────────────────┐
│   RTMS Service  │
│  (Data Source)  │
└────────┬────────┘
         │ Publishes events
         ↓
┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Event Router   │────→│ Event Store  │←───→│ Historical Replay   │
│  (Kafka/Redis)  │     │    (S3)      │     │     Service         │
└────────┬────────┘     └──────────────┘     └─────────────────────┘
         │ Fan-out to all subscribers
    ┌────┴────┬────────┬────────┬────────┬────────┐
    ↓         ↓        ↓        ↓        ↓        ↓
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Talk    ││Inter-  ││Speech  ││Engage- ││Silence ││  New   │
│Time    ││ruption ││Pace    ││ment    ││Detect  ││Service │
│Service ││Service ││Service ││Service ││Service ││  ...   │
└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
    ↓         ↓        ↓        ↓        ↓        ↓
┌──────────────────────────────────────────────────────────┐
│           Analytics Database (PostgreSQL)                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Time-series Tables with Partitioning               │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
    ↓ Materialized views
┌──────────────────────────────────────────────────────────┐
│              Redis Cache Layer                           │
│  Hot data, aggregations, real-time counters             │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│              Analytics Query API                         │
│  GraphQL endpoint with DataLoader pattern               │
└──────────────────────────────────────────────────────────┘
```

## Event Schema

### Base Event Structure
```json
{
  "eventId": "uuid",
  "eventType": "audio|video|transcript|session|participant",
  "sessionId": "session_uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    // Event-specific payload
  },
  "metadata": {
    "rtmsStreamId": "stream_id",
    "processingTime": "2024-01-15T10:30:00.100Z",
    "version": "1.0"
  }
}
```

### Event Types

#### Audio Event
```json
{
  "eventType": "audio",
  "data": {
    "participantId": "participant_uuid",
    "userId": "zoom_user_id",
    "userName": "John Doe",
    "chunkId": "chunk_uuid",
    "duration": 20,
    "s3Key": "audio/session_id/timestamp_chunk_001.pcm16",
    "size": 640,
    "sampleRate": 16000,
    "channels": 1
  }
}
```

#### Transcript Event
```json
{
  "eventType": "transcript",
  "data": {
    "participantId": "participant_uuid",
    "userId": "zoom_user_id",
    "userName": "John Doe",
    "text": "Hello everyone, let's begin",
    "startTime": 10.5,
    "endTime": 12.3,
    "confidence": 0.95,
    "language": "en"
  }
}
```

## Microservice Templates

### Base Analytics Service (Python)
```python
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any
import redis
import json

class BaseAnalyticsService(ABC):
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.redis_client = redis.Redis(decode_responses=True)
        self.event_types = []
        
    async def start(self):
        """Subscribe to events and start processing"""
        pubsub = self.redis_client.pubsub()
        
        # Subscribe to relevant event types
        for event_type in self.event_types:
            pubsub.subscribe(f"rtms:events:{event_type}")
        
        # Process events
        async for message in self.listen_events(pubsub):
            if message['type'] == 'message':
                await self.process_event(json.loads(message['data']))
    
    @abstractmethod
    async def process_event(self, event: Dict[str, Any]):
        """Process a single event"""
        pass
    
    @abstractmethod
    def get_event_types(self) -> list:
        """Return list of event types this service processes"""
        pass
    
    async def publish_metric(self, metric_name: str, value: Any, tags: Dict[str, str]):
        """Publish computed metric"""
        metric = {
            "service": self.service_name,
            "metric": metric_name,
            "value": value,
            "tags": tags,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in time-series table
        await self.store_metric(metric)
        
        # Update cache for real-time access
        cache_key = f"metric:{metric_name}:{tags.get('session_id')}:{tags.get('participant_id', 'all')}"
        self.redis_client.setex(cache_key, 300, json.dumps(metric))
```

### Talk Time Analytics Service
```python
class TalkTimeAnalyticsService(BaseAnalyticsService):
    def __init__(self):
        super().__init__("talk_time_analytics")
        self.event_types = ["audio", "transcript"]
        self.active_speakers = {}  # Track speaking state
        
    async def process_event(self, event: Dict[str, Any]):
        if event['eventType'] == 'audio':
            await self.process_audio_event(event)
        elif event['eventType'] == 'transcript':
            await self.process_transcript_event(event)
    
    async def process_audio_event(self, event: Dict[str, Any]):
        """Track speaking time from audio chunks"""
        session_id = event['sessionId']
        participant_id = event['data']['participantId']
        duration = event['data']['duration'] / 1000  # Convert to seconds
        
        # Increment talk time counter
        talk_time_key = f"talk_time:{session_id}:{participant_id}"
        current_time = float(self.redis_client.get(talk_time_key) or 0)
        new_time = current_time + duration
        
        self.redis_client.setex(talk_time_key, 3600, new_time)
        
        # Publish metric
        await self.publish_metric(
            "talk_time_seconds",
            new_time,
            {
                "session_id": session_id,
                "participant_id": participant_id,
                "user_name": event['data']['userName']
            }
        )
        
        # Calculate participation percentage
        total_key = f"talk_time:{session_id}:total"
        total_time = float(self.redis_client.get(total_key) or 0) + duration
        self.redis_client.setex(total_key, 3600, total_time)
        
        participation_pct = (new_time / total_time * 100) if total_time > 0 else 0
        
        await self.publish_metric(
            "participation_percentage",
            participation_pct,
            {
                "session_id": session_id,
                "participant_id": participant_id
            }
        )
```

### Interruption Detection Service
```python
class InterruptionDetectionService(BaseAnalyticsService):
    def __init__(self):
        super().__init__("interruption_detection")
        self.event_types = ["audio", "transcript"]
        self.speaking_windows = {}  # Track who's speaking when
        
    async def process_event(self, event: Dict[str, Any]):
        session_id = event['sessionId']
        participant_id = event['data']['participantId']
        timestamp = event['timestamp']
        
        # Get current speakers
        session_speakers = self.speaking_windows.get(session_id, {})
        
        # Check for overlaps (interruptions)
        interruptions = []
        for other_participant, windows in session_speakers.items():
            if other_participant != participant_id:
                for window in windows:
                    if self.is_overlap(timestamp, window):
                        interruptions.append({
                            "interrupter": participant_id,
                            "interrupted": other_participant,
                            "timestamp": timestamp
                        })
        
        # Update speaking windows
        if participant_id not in session_speakers:
            session_speakers[participant_id] = []
        
        session_speakers[participant_id].append({
            "start": timestamp,
            "end": timestamp + event['data'].get('duration', 1000) / 1000
        })
        
        # Clean old windows (keep last 10 seconds)
        self.clean_old_windows(session_speakers, timestamp)
        
        # Publish interruption metrics
        for interruption in interruptions:
            await self.publish_metric(
                "interruption",
                1,
                {
                    "session_id": session_id,
                    "interrupter_id": interruption["interrupter"],
                    "interrupted_id": interruption["interrupted"],
                    "timestamp": interruption["timestamp"]
                }
            )
```

## Service Discovery & Registration

```yaml
# service-registry.yaml
services:
  talk_time_analytics:
    image: analytics/talk-time:latest
    replicas: 3
    events: ["audio", "transcript"]
    metrics: ["talk_time_seconds", "participation_percentage"]
    
  interruption_detection:
    image: analytics/interruption:latest
    replicas: 2
    events: ["audio", "transcript"]
    metrics: ["interruption_count", "interruption_pattern"]
    
  speech_pace_analytics:
    image: analytics/speech-pace:latest
    replicas: 2
    events: ["transcript"]
    metrics: ["words_per_minute", "pace_variation"]
    
  # Add new services here without changing architecture
  sentiment_analysis:
    image: analytics/sentiment:latest
    replicas: 4
    events: ["transcript"]
    metrics: ["sentiment_score", "emotion_detection"]
```

## Deployment Pattern

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ service_name }}
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ service_name }}
  template:
    metadata:
      labels:
        app: {{ service_name }}
        type: analytics-microservice
    spec:
      containers:
      - name: {{ service_name }}
        image: {{ image }}
        env:
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Query API Design

### GraphQL Schema
```graphql
type Query {
  # Get specific metric
  metric(
    name: String!
    sessionId: ID!
    participantId: ID
    timeRange: TimeRange
  ): Metric
  
  # Get multiple metrics
  metrics(
    names: [String!]!
    sessionId: ID!
    participantIds: [ID]
    timeRange: TimeRange
  ): [Metric]
  
  # Get aggregated analytics
  sessionAnalytics(
    sessionId: ID!
    includeMetrics: [String!]
  ): SessionAnalytics
}

type Metric {
  name: String!
  value: Float!
  unit: String
  timestamp: DateTime!
  tags: JSON
  history(limit: Int): [MetricPoint]
}

type SessionAnalytics {
  sessionId: ID!
  duration: Int!
  participants: [ParticipantAnalytics]!
  aggregates: JSON
}

type ParticipantAnalytics {
  participantId: ID!
  name: String
  metrics: [Metric]!
}
```

### Query Example
```graphql
query GetMeetingAnalytics($sessionId: ID!) {
  sessionAnalytics(
    sessionId: $sessionId
    includeMetrics: [
      "talk_time_seconds",
      "participation_percentage",
      "interruption_count",
      "words_per_minute"
    ]
  ) {
    duration
    participants {
      participantId
      name
      metrics {
        name
        value
        history(limit: 100) {
          timestamp
          value
        }
      }
    }
  }
}
```

## Performance Optimizations

### 1. Read Path Optimization
```python
# Cache-first approach
async def get_metric(metric_name: str, session_id: str, participant_id: str = None):
    # Try cache first
    cache_key = f"metric:{metric_name}:{session_id}:{participant_id or 'all'}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database
    result = await db.query_metric(metric_name, session_id, participant_id)
    
    # Update cache
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
```

### 2. Write Path Optimization
```python
# Batch writes for efficiency
class MetricBatcher:
    def __init__(self, batch_size=100, flush_interval=1.0):
        self.batch = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        asyncio.create_task(self.periodic_flush())
    
    async def add_metric(self, metric):
        self.batch.append(metric)
        if len(self.batch) >= self.batch_size:
            await self.flush()
    
    async def flush(self):
        if not self.batch:
            return
        
        # Bulk insert to database
        await db.bulk_insert_metrics(self.batch)
        
        # Update cache for recent metrics
        for metric in self.batch[-10:]:  # Keep last 10 in cache
            cache_key = self.get_cache_key(metric)
            redis_client.setex(cache_key, 300, json.dumps(metric))
        
        self.batch = []
```

### 3. Horizontal Scaling
- Each service can scale independently
- Use consistent hashing for event distribution
- Partition data by session_id for locality
- Use read replicas for query load

## Adding New Analytics Services

### Step 1: Define the Service
```python
# emotion_analytics_service.py
class EmotionAnalyticsService(BaseAnalyticsService):
    def __init__(self):
        super().__init__("emotion_analytics")
        self.event_types = ["audio"]
        self.emotion_model = load_emotion_model()
    
    async def process_event(self, event: Dict[str, Any]):
        if event['eventType'] == 'audio':
            # Download audio chunk from S3
            audio_data = await self.download_audio(event['data']['s3Key'])
            
            # Analyze emotion
            emotion_scores = self.emotion_model.analyze(audio_data)
            
            # Publish metrics
            for emotion, score in emotion_scores.items():
                await self.publish_metric(
                    f"emotion_{emotion}",
                    score,
                    {
                        "session_id": event['sessionId'],
                        "participant_id": event['data']['participantId'],
                        "timestamp": event['timestamp']
                    }
                )
```

### Step 2: Create Docker Image
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY emotion_analytics_service.py .
CMD ["python", "emotion_analytics_service.py"]
```

### Step 3: Deploy
```bash
# Build and push
docker build -t analytics/emotion:latest .
docker push analytics/emotion:latest

# Add to service registry
kubectl apply -f emotion-analytics-deployment.yaml
```

### Step 4: Query New Metrics
```graphql
query GetEmotions($sessionId: ID!) {
  metrics(
    names: ["emotion_happy", "emotion_sad", "emotion_angry"]
    sessionId: $sessionId
  ) {
    name
    value
    timestamp
  }
}
```

## Monitoring & Observability

### Service Health Dashboard
```yaml
metrics:
  - name: events_processed_total
    type: counter
    labels: [service, event_type]
    
  - name: processing_duration_seconds
    type: histogram
    labels: [service, event_type]
    
  - name: active_sessions
    type: gauge
    labels: [service]
    
  - name: error_rate
    type: counter
    labels: [service, error_type]
```

### Distributed Tracing
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_event(self, event: Dict[str, Any]):
    with tracer.start_as_current_span(
        "process_event",
        attributes={
            "event.type": event['eventType'],
            "session.id": event['sessionId'],
            "service.name": self.service_name
        }
    ) as span:
        # Process event
        result = await self.analyze_event(event)
        span.set_attribute("result.metrics_count", len(result))
        return result
```

## Failure Handling

### Circuit Breaker Pattern
```python
from circuit_breaker import CircuitBreaker

class AnalyticsService:
    def __init__(self):
        self.db_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=DatabaseError
        )
    
    @self.db_breaker
    async def store_metric(self, metric):
        """Store with circuit breaker protection"""
        return await self.db.insert_metric(metric)
    
    async def process_event(self, event):
        try:
            metric = await self.compute_metric(event)
            
            # Try to store, fallback to cache if circuit is open
            if self.db_breaker.current_state == 'open':
                await self.cache_metric_for_retry(metric)
            else:
                await self.store_metric(metric)
                
        except Exception as e:
            # Log but don't crash - other services continue
            logger.error(f"Failed to process event: {e}")
            await self.dead_letter_queue.add(event)
```

## Cost Optimization

### Resource Allocation by Service Priority
```yaml
service_tiers:
  critical:  # Always running, high resources
    - talk_time_analytics
    - interruption_detection
    resources:
      cpu: "500m"
      memory: "512Mi"
      replicas: 3
      
  important:  # Always running, moderate resources
    - speech_pace_analytics
    - engagement_analytics
    resources:
      cpu: "250m"
      memory: "256Mi"
      replicas: 2
      
  optional:  # Can scale to zero when idle
    - sentiment_analysis
    - emotion_detection
    resources:
      cpu: "100m"
      memory: "128Mi"
      replicas: 0-5  # Scale based on load
```

## Conclusion

This architecture enables:
1. **Zero latency impact** through asynchronous processing
2. **Infinite scalability** by adding services without architectural changes
3. **Fault isolation** preventing cascade failures
4. **Cost efficiency** through resource tiering
5. **Easy deployment** of new analytics types

The event-driven design with CQRS pattern ensures that adding new analytics services never impacts the core RTMS data flow, while the cache-first query approach maintains fast read performance regardless of the number of analytics services.