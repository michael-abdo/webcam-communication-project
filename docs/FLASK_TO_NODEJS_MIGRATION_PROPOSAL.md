# Flask to Node.js Migration Proposal

## Executive Summary

This document outlines a proposal to migrate the Python/Flask web layer of the Phase-2 application to Node.js while maintaining Python microservices for scientific computing components.

## Current Architecture

The application currently uses a hybrid architecture:

### Python/Flask Application
- **Framework**: Flask with SQLAlchemy
- **Database**: PostgreSQL/SQLite with SQLAlchemy ORM  
- **Size**: 18,600 lines of code across 78 files
- **Deployment**: Gunicorn with gevent workers

### Node.js RTMS Service
- **Framework**: Express.js
- **Purpose**: Real-time media streaming from Zoom meetings
- **SDK**: Zoom RTMS SDK (`@zoom/rtms`)

## Proposed Architecture

```
┌─────────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Node.js API Server    │     │  Node.js RTMS       │     │  Python Services    │
│   (Express)             │     │  Service            │     │  (Microservices)    │
│                         │     │                     │     │                     │
│ - All REST APIs         │     │ - Zoom webhooks     │     │ - Fatigue detection │
│ - Database models       │ ←───┤ - Media streaming   │     │ - Video analysis    │
│ - Business logic        │     │ - Transcripts       │     │ - OpenCV processing │
│ - WebSocket handling    │     │                     │     │ - ML algorithms     │
│ - Static file serving   │     │                     │     │                     │
└─────────────────────────┘     └─────────────────────┘     └─────────────────────┘
         ↓                               ↓                            ↑
    PostgreSQL                      S3 Storage                 HTTP/gRPC calls
```

## Migration Scope

### What Moves to Node.js

1. **All Flask Blueprints → Express Routes**
   - `analytics_api` → `/routes/analytics.js`
   - `capture_api` → `/routes/capture.js`
   - `meetings_api` → `/routes/meetings.js`
   - `zoom_api` → `/routes/zoom.js`
   - `rtms_ingest_api` → `/routes/rtms.js`

2. **SQLAlchemy Models → Prisma/Sequelize**
   - Session management
   - Participant tracking
   - Media chunk storage
   - Meeting analytics
   - Transcription segments

3. **Business Logic Services**
   - Capture service logic
   - Analytics computation
   - Session state management
   - S3 operations
   - WebSocket broadcasting

### What Stays in Python

1. **Scientific Computing Components**
   - Fatigue detection algorithms
   - OpenCV video processing
   - MediaPipe facial landmark detection
   - PERCLOS calculations
   - Blink rate analysis

2. **Machine Learning Features**
   - Complex algorithmic processing
   - NumPy-based calculations
   - Research-validated thresholds

## Implementation Timeline

### Full Migration: 6-10 weeks

#### Week 1-2: Foundation & Setup
- Set up Node.js project structure
- Choose and configure ORM (Prisma recommended)
- Migrate database schema
- Set up testing framework
- Create base middleware (auth, error handling)

#### Week 3-4: Core Models & Simple APIs
- Port SQLAlchemy models → Prisma schema
- Migrate basic CRUD endpoints
- Set up S3 integration
- Implement logging and monitoring

#### Week 5-6: Complex Business Logic
- Port capture service logic
- Migrate analytics computation
- Port meeting management
- WebSocket hub implementation
- Real-time frame broadcasting

#### Week 7-8: Python Service Integration
- Set up Python microservice for fatigue detection
- Create API bridge between Node.js ↔ Python
- Implement service communication
- Error handling and retry logic

#### Week 9-10: Testing & Deployment
- Integration testing
- Performance testing
- Parallel deployment
- Gradual traffic migration
- Bug fixes and optimization

### Incremental Migration Alternative: 4-6 weeks

#### Phase 1 (Week 1-2): New Features Only
- Build new endpoints in Node.js
- Keep existing Flask running
- Use nginx to route between them

#### Phase 2 (Week 3-4): Migrate Simple APIs
- Move read-only endpoints first
- Sessions, participants queries
- Analytics retrieval

#### Phase 3 (Week 5-6): Complex Features
- Move write operations
- WebSocket handling
- Python service integration

## Technical Approach

### ORM Migration Example

**Current SQLAlchemy Model:**
```python
class Session(Base):
    __tablename__ = "sessions"
    
    id = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    meeting_uuid = mapped_column(String(255), nullable=True)
    stream_id = mapped_column(String(255), nullable=True)
    participants = relationship("Participant", back_populates="session")
```

**New Prisma Model:**
```prisma
model Session {
  id            String   @id @default(uuid())
  meetingUuid   String?
  streamId      String?
  participants  Participant[]
  mediaChunks   MediaChunk[]
  transcript    SessionTranscript?
  createdAt     DateTime @default(now())
}
```

### API Migration Example

**Current Flask Route:**
```python
@analytics_api.route("/meetings/<meeting_id>", methods=["GET"])
def get_analytics(meeting_id: str):
    analytics = get_meeting_analytics(meeting_id)
    return jsonify(analytics), HTTPStatus.OK
```

**New Express Route:**
```javascript
router.get('/meetings/:meetingId', async (req, res) => {
    try {
        const analytics = await analyticsService.getAnalytics(req.params.meetingId);
        res.json(analytics);
    } catch (error) {
        res.status(404).json({ error: error.message });
    }
});
```

### Python Service Communication

```javascript
// Node.js calling Python fatigue detection service
async function analyzeFatigue(videoData) {
    const response = await fetch('http://python-service:5000/analyze/fatigue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_data: videoData })
    });
    
    if (!response.ok) {
        throw new Error(`Fatigue analysis failed: ${response.statusText}`);
    }
    
    return response.json();
}
```

## Resource Requirements

### Team Composition
- **1 Senior Full-Stack Developer** (Node.js expert)
- **1 Mid-level Developer** 
- **0.5 DevOps Engineer** (deployment and infrastructure)

### Solo Developer Timeline
- Add 50% to all estimates (9-15 weeks total)
- Higher risk of bugs and missed edge cases

## Cost-Benefit Analysis

### Estimated Costs
- **Development Time**: 6-10 weeks
- **Developer Cost**: $30,000 - $60,000 (assuming $150k/year developers)
- **Infrastructure Changes**: Minimal
- **Testing & QA**: Additional 1-2 weeks

### Benefits
1. **Unified JavaScript ecosystem** for web layer
2. **Better async performance** for I/O operations
3. **Easier hiring** - more Node.js developers available
4. **Simplified deployment** - fewer runtime dependencies
5. **Better real-time capabilities** with native WebSocket support

### Risks
1. **Migration bugs** affecting production
2. **Performance regression** if not optimized properly
3. **Learning curve** for Python-focused team
4. **Maintaining two codebases** during transition

## Recommendation

### When to Migrate
✅ **Proceed with migration if:**
- You're experiencing Flask performance bottlenecks
- Python developers are hard to find/expensive
- You need better real-time features
- Team has strong Node.js expertise
- You have budget and time for migration

### When to Keep Hybrid Architecture
❌ **Stay with current setup if:**
- Current system meets performance needs
- Team is Python-focused
- Budget is limited
- Need to deliver features quickly
- Planning more ML/AI features (Python ecosystem advantage)

## Migration Checklist

- [ ] Assess team Node.js expertise
- [ ] Create detailed API inventory
- [ ] Set up Node.js project template
- [ ] Choose ORM (Prisma vs Sequelize)
- [ ] Plan database migration strategy
- [ ] Design Python microservice architecture
- [ ] Set up CI/CD for Node.js
- [ ] Create migration runbook
- [ ] Plan rollback strategy
- [ ] Allocate QA resources

## Conclusion

The Flask to Node.js migration is technically feasible but represents a significant investment. The hybrid architecture currently in use is actually well-designed, using Python for scientific computing where it excels and Node.js for real-time streaming.

Unless there are specific pain points with Flask performance or developer availability, the 6-10 week investment might be better spent on new features and improvements to the existing system.

If migration is desired, the incremental approach is recommended to minimize risk and allow for course correction based on initial results.