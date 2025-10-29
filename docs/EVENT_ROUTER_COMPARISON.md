# Event Router Comparison: Redis vs Kafka

## Decision: Redis Pub/Sub

### Why Redis for Phase 2 Analytics:

1. **Already in tech stack** - Planned for Phase 3 caching
2. **Simpler to operate** - Single binary, minimal configuration
3. **Lower latency** - Sub-millisecond pub/sub
4. **Sufficient for current scale** - Handles 100k+ messages/second
5. **Easy local development** - Single Docker container

### Comparison Matrix

| Feature | Redis | Kafka | Winner for Phase 2 |
|---------|-------|-------|-------------------|
| **Setup Complexity** | Simple (1 container) | Complex (Zookeeper + brokers) | ✅ Redis |
| **Message Durability** | Optional (RDB/AOF) | Built-in (log-based) | Kafka |
| **Replay Capability** | Manual (with Streams) | Native | Kafka |
| **Latency** | < 1ms | 2-5ms | ✅ Redis |
| **Throughput** | 100k msg/s | 1M+ msg/s | Kafka |
| **Operational Overhead** | Low | High | ✅ Redis |
| **Memory Usage** | High (in-memory) | Lower (disk-based) | Kafka |
| **Client Libraries** | Excellent | Excellent | Tie |

### Implementation Plan with Redis

```javascript
// RTMS Service publishes events
const redis = new Redis();

// Publish with channel-based routing
redis.publish('rtms:events:audio', JSON.stringify(audioEvent));
redis.publish('rtms:events:transcript', JSON.stringify(transcriptEvent));
redis.publish('rtms:events:video', JSON.stringify(videoEvent));
```

```python
# Analytics services subscribe to channels
redis_client = redis.Redis()
pubsub = redis_client.pubsub()
pubsub.subscribe('rtms:events:audio', 'rtms:events:transcript')

for message in pubsub.listen():
    process_event(json.loads(message['data']))
```

### When to Migrate to Kafka

Consider Kafka when:
- Need guaranteed message delivery
- Processing millions of events/minute
- Require long-term event storage
- Need complex event routing
- Building event sourcing architecture

### Hybrid Approach for Future

```
RTMS → Redis Pub/Sub → Analytics Services (real-time)
  ↓
  → S3 Event Store → Kafka (batch replay)
```

## Decision: Start with Redis, add Kafka later if needed