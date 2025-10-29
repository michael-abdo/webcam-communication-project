# RTMS Analytics Platform

A real-time media streaming analytics platform built for Zoom integration, providing live audio processing and speaker analytics.

## Overview

This is a focused RTMS-only implementation that provides:
- **Real-time audio processing** from Zoom Media Streams
- **Live speaker analytics** including talk time and participation metrics
- **WebSocket dashboard** for real-time monitoring
- **Redis-based event streaming** for scalable analytics processing

## Architecture

### Core Components

1. **RTMS Service** (`src/rtms-service/`)
   - Node.js service that connects to Zoom RTMS
   - Processes audio streams and publishes events to Redis
   - Handles Zoom webhooks and media stream management

2. **Analytics Engine** (`src/analytics/`)
   - Python-based analytics processing
   - Calculates talk time, participation metrics
   - Real-time event processing via Redis pub/sub

3. **Web Dashboard** (`src/web/`)
   - Flask web application
   - Real-time RTMS dashboard with WebSocket updates
   - REST APIs for analytics data

4. **Database Models** (`src/models/`)
   - SQLAlchemy models for sessions and analytics data
   - PostgreSQL support for production

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis
- PostgreSQL (production)

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install --prefix src/rtms-service
   ```

3. **Set environment variables:**
   ```bash
   export ZM_RTMS_CLIENT="your_zoom_rtms_client_id"
   export ZM_RTMS_SECRET="your_zoom_rtms_secret"
   export REDIS_URL="redis://localhost:6379"
   export DATABASE_URL="postgresql://user:pass@localhost/dbname"
   ```

### Development

**Start all services:**
```bash
# Start Redis
redis-server

# Start Analytics Worker
python src/analytics/talk_time_analytics.py

# Start RTMS Service  
node src/rtms-service/index.js

# Start Web App
python -c "from src.web.app import app; app.run(debug=True)"
```

### Production (Heroku)

The application is configured for Heroku deployment with the following processes:

```yaml
web: gunicorn -k gevent --worker-connections 100 --workers 1 --bind 0.0.0.0:$PORT src.web.app:app
rtms: node src/rtms-service/index.js  
worker: python src/analytics/talk_time_analytics.py
```

## API Endpoints

### RTMS Dashboard
- `GET /rtms/ui` - Real-time dashboard with live analytics

### Analytics API
- `GET /api/analytics/sessions` - List recent sessions
- `GET /api/analytics/sessions/{id}` - Get session analytics
- `GET /test-analytics` - Test analytics functionality

### RTMS Integration
- `POST /api/rtms/webhook` - Zoom RTMS webhook endpoint
- `GET /api/rtms/pending-webhooks` - Check webhook status

## Features

### Real-time Analytics
- **Talk Time Tracking**: Measure individual speaker time
- **Participation Metrics**: Calculate speaking equality and balance
- **Live Updates**: WebSocket-powered real-time dashboard updates

### Zoom Integration
- **RTMS Webhooks**: Automatic session start/stop handling
- **Audio Processing**: Real-time audio stream analysis
- **Session Management**: Automatic meeting lifecycle tracking

### Scalable Architecture
- **Redis Events**: Pub/sub event streaming for horizontal scaling
- **Microservices**: Separate RTMS, analytics, and web services
- **Cloud Ready**: Heroku/AWS deployment support

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ZM_RTMS_CLIENT` | Zoom RTMS Client ID | Yes |
| `ZM_RTMS_SECRET` | Zoom RTMS Secret | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `PORT` | Web server port | No (default: 5000) |
| `RTMS_SERVICE_PORT` | RTMS service port | No (default: 8080) |

## Technologies

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **RTMS Service**: Node.js, Express, Zoom RTMS SDK
- **Analytics**: Redis, Python asyncio
- **Database**: PostgreSQL, Redis
- **Frontend**: Vanilla JavaScript, WebSockets
- **Deployment**: Heroku, Gunicorn

## License

MIT License - see LICENSE file for details.

---

**Note**: This is a streamlined RTMS-only version. All legacy Phase-1 components (assessments, baseline capture, cognitive overload detection) have been removed for clarity and maintainability.