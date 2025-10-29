# RTMS Analytics Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node-%3E%3D16.0.0-green.svg)](https://nodejs.org/)
[![Heroku](https://img.shields.io/badge/deploy-heroku-purple.svg)](https://heroku.com)

> Real-time Media Stream Analytics Platform with live talk-time tracking, participant equality metrics, and WebSocket-based dashboards.

## 🚀 Features

- **Real-time Analytics** - Live talk time and participation tracking
- **WebSocket Dashboard** - Real-time data visualization
- **Zoom RTMS Integration** - Direct media stream processing
- **Redis Pub/Sub** - Scalable event streaming
- **Microservices Architecture** - Modular analytics services
- **Production Ready** - Deployed and tested on Heroku

## 🏗️ Foundation-First Architecture

This system is built on a **test-driven, foundation-first approach**. Every feature builds upon proven, working camera fundamentals. The camera health test is the **bedrock** - it must pass before any other functionality can be trusted.

## 🧪 Test Hierarchy (Bottom-Up)

```
🏢 Advanced Features (Fatigue Detection, Analysis)
├── 📹 Live Video Streaming & Dashboards  
├── 📊 Health Monitoring & Diagnostics
├── 🔧 Camera Quality & Performance Tests
└── 🎯 CAMERA HEALTH TEST ← FOUNDATION (MUST PASS FIRST)
```

## 📁 Directory Structure

### Organized Project Layout (CLEANED)
```
📦 RTMS Analytics Platform/
├── 📄 README.md              # Project documentation (you are here)
├── 📄 requirements.txt       # Python dependencies
├── 📄 runtime.txt           # Python version for Heroku
├── 📄 package.json          # Node.js dependencies (RTMS service)
├── 📄 Procfile              # Heroku deployment config
├── 📄 .env.example          # Environment variables template
├── 📄 .gitignore            # Git ignore rules
├── 📄 .slugignore           # Heroku ignore rules
│
├── 🐍 app_lightweight.py    # Main Flask application
├── 🐍 config.py             # Application configuration
├── 🐍 core_pipeline.py      # Core system pipeline
├── 🐍 start_system.py       # System startup script
│
├── 📁 analytics_services/   # Analytics microservices
│   ├── talk_time_analytics.py # Real-time talk time tracking
│   ├── base_analytics_service.py
│   └── ... (analytics modules)
│
├── 📁 blueprints/           # Flask blueprints
│   ├── analytics_api.py     # Analytics API endpoints
│   ├── rtms_ingest_api.py   # RTMS ingestion API
│   ├── rtms_ui.py           # RTMS dashboard UI
│   └── ... (other blueprints)
│
├── 📁 rtms-service/         # Real-time Media Service (Node.js)
│   ├── index.js             # RTMS WebSocket service
│   ├── eventPublisher.js    # Redis event publisher
│   ├── package.json         # Node.js dependencies
│   └── public/              # RTMS dashboard frontend
│
├── 📁 deployment/           # Deployment configurations
│   ├── 📁 configs/          # Platform-specific configs
│   │   ├── docker-compose.yml
│   │   ├── fly.toml, netlify.toml, etc.
│   └── 📁 scripts/          # Deployment scripts
│       ├── deploy_analytics_heroku.sh
│       └── ... (deployment scripts)
│
├── 📁 docs/                 # Documentation
│   ├── 📁 planning/         # Planning documents
│   │   ├── DATABASE_SCHEMA_PLAN.md
│   │   └── ... (planning docs)
│   ├── 📁 deployment/       # Deployment guides
│   └── ... (other documentation)
│
├── 📁 tests/                # Test files
│   ├── 📁 integration/      # Integration tests
│   │   ├── test_*.py, test_*.js, test_*.sh
│   └── 📁 definitions/      # Test definitions
│
├── 📁 models/               # Database models
├── 📁 services/             # Core services
├── 📁 static/               # Static assets
├── 📁 templates/            # HTML templates
└── 📁 credentials/          # Credential files (gitignored)
```
├── 📁 camera_tools/         # Camera foundation & health
├── 📁 cognitive_overload/   # Fatigue detection core
├── 📁 assessments/          # Psychological assessments
├── 📁 ai/                   # AI/ML components
├── 📁 apis/                 # External API integrations
├── 📁 streaming/            # S3 streaming functionality
├── 📁 static/               # Frontend assets (JS, CSS)
├── 📁 templates/            # HTML templates
└── 📁 data/                 # Data files and results
```

### Key Components
- **Core Application**: `app_lightweight.py` - Main Flask web server
- **Foundation**: `camera_tools/` - Camera health and diagnostics (BEDROCK)
- **Features**: `cognitive_overload/`, `assessments/` - Core functionality
- **Infrastructure**: `deployment/`, `scripts/`, `tests/` - Supporting tools
- **Documentation**: `docs/` - All project documentation centralized

## 🚀 Quick Start (Foundation-First)

### Step 1: Validate Camera Foundation (REQUIRED)
```bash
# ALWAYS run this first - everything depends on camera health
cd camera_tools/tests
python3 quick_camera_test.py
```

**✅ Expected Result:**
```
✅ Camera Status: ACTIVE
✅ Found working camera(s): [0, 1] 
🎬 Foundation: SOLID
```

**❌ If this fails, STOP. Fix camera issues before proceeding.**

### Step 2: Health Monitoring (Built on Foundation)
```bash
# Only run after camera health passes
cd camera_tools/health_monitoring
python3 webcam_health_monitor.py
```

### Step 3: Live Dashboard (Built on Health)
```bash
# Only run after health monitoring works
cd camera_tools/dashboards
python3 camera_status_dashboard.py
# Access: http://localhost:5002
```

### Step 4: Advanced Features (Built on Everything)
```bash
# Basic Fatigue Detection Dashboard (no MediaPipe required)
python3 basic_fatigue_dashboard.py
# Access: http://localhost:5001

# Advanced Fatigue Detection (requires MediaPipe)
python3 demo_dashboard.py
# Access: http://localhost:5000
```

## 📦 Data Persistence

- The service now persists capture sessions, participants, and chunk manifests in a SQL database.
- In production (Heroku, AWS), point `DATABASE_URL` at a managed PostgreSQL instance (e.g. Heroku Postgres, Amazon RDS).
- For local development the app automatically falls back to a SQLite database stored under `data/app.db`.
- When provisioning Postgres make sure the role has privileges to create tables; tables are auto-created on boot via SQLAlchemy.

## 🌐 Phase 1 Capture API

These endpoints back the facilitator capture flow and mirror the Phase 1 spec.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/sessions` | `POST` | Create capture session with facilitator metadata + consent timestamp |
| `/api/sessions/<id>/participants` | `POST` | Register facilitator device readiness for the session |
| `/api/sessions/<id>/chunks` | `POST` | Persist chunk manifest (sequence, checksum, S3 key) after upload |
| `/api/sessions/<id>` | `GET` | Retrieve a session with participants and uploaded chunk manifest |

Example session creation payload:

```json
{
  "facilitator_id": "fac-123",
  "consent_at": "2024-01-15T18:42:00Z",
  "device_kind": "macbook-pro",
  "locale": "en-US"
}
```

> **Auth:** Set `CAPTURE_API_TOKEN` in the environment to enforce facilitator authentication. The capture UI now prompts for this value and injects it into all Phase 1 API requests per the spec’s “Auth & Data” requirement.

### Telemetry & Alerts

- Enable `METRICS_ENABLED=true` to activate StatsD metrics.
- Configure `METRICS_STATSD_HOST`, `METRICS_STATSD_PORT`, and optional `METRICS_PREFIX` to point at your metrics backend.
- Successful chunk uploads emit `phase1.chunk.uploaded`; failures emit `phase1.chunk.failed`/`phase1.chunk.conflict`, with latency timings under `phase1.chunk.upload_latency_ms`.
- Build alerts on sustained failures to match the Phase 1 telemetry requirement.
- `DATABASE_URL` is automatically rewritten from `postgres://` to `postgresql+psycopg2://` at runtime for SQLAlchemy compatibility.

### Reviewer Dashboard

- Visit `/phase1/sessions` to open the Phase 1 validation UI.
- Provide the same capture API token to enumerate recent sessions (limit configurable in the UI).
- Select a session to review facilitator metadata, participant readiness, chunk manifest, transcript/log statuses, and grab time-limited download links for raw media or artifacts.
- This replaces the in-memory `/tests/results` view and reflects the persisted capture data in Postgres.

### Transcript & Log APIs

- `POST /api/sessions/<id>/transcript` – ingest transcript metadata and optional file upload (`status`, optional `storage_key`, `mime_type`, `generated_at`).
- `POST /api/sessions/<id>/logs` – record processing logs with status/message and optional upload payload.
- `GET /api/sessions/<id>/transcript/download` – retrieve signed URL for the latest transcript artifact.
- `GET /api/sessions/<id>/logs/<log_id>/download` – retrieve signed URL for a stored log artifact.

## 🔍 Test-Driven Validation

### Foundation Test (Layer 0)
```bash
cd camera_tools/tests
python3 quick_camera_test.py
```
**Purpose**: Verify camera hardware access, frame capture, basic functionality  
**Must Pass**: YES - Nothing works without this

### Quality Tests (Layer 1)  
```bash
cd camera_tools/tests
python3 camera_quality_test.py
```
**Purpose**: Resolution support, FPS consistency, image quality  
**Must Pass**: Before proceeding to monitoring

### Health Monitoring (Layer 2)
```bash
cd camera_tools/health_monitoring
python3 webcam_health_monitor.py
```
**Purpose**: Continuous health tracking, metrics collection  
**Must Pass**: Before live streaming

### Live Streaming (Layer 3)
```bash
cd camera_tools/dashboards
python3 camera_status_dashboard.py
```
**Purpose**: Real-time video feed, web interface  
**Must Pass**: Before advanced features

### Advanced Features (Layer 4)
```bash
# Basic fatigue detection (motion-based simulation)
python3 basic_fatigue_dashboard.py

# Full fatigue detection (MediaPipe face tracking)
python3 demo_dashboard.py
```
**Purpose**: Fatigue detection, PERCLOS monitoring, progressive alerts  
**Built On**: All previous layers

## 🏗️ Why Foundation-First?

### 1. **Solid Base**
- Camera health issues cascade upward
- Fix hardware problems before software features
- Prevents building on broken foundations

### 2. **Clear Dependencies**
- Each layer depends on the layer below
- Failed foundation = everything fails
- Test bottom-up, deploy top-down

### 3. **Reliable Debugging**
- Issues isolated to specific layers
- Foundation test = first diagnostic step
- Clear failure points and fixes

### 4. **Production Confidence**
- Camera health verified before deployment
- Each layer validated independently
- Proven reliability stack

## 📋 Camera Tools Suite

### Foundation Tests
- `camera_tools/tests/quick_camera_test.py` - **BEDROCK TEST**
- `camera_tools/tests/camera_quality_test.py` - Quality validation
- `camera_tools/diagnostics/camera_diagnostics.py` - Deep analysis
- `camera_tools/diagnostics/check_camera_permissions.py` - System permissions

### Health & Monitoring
- `camera_tools/health_monitoring/webcam_health_monitor.py` - Continuous monitoring
- `camera_tools/dashboards/camera_status_dashboard.py` - Live dashboard

### Central Runner
- `camera_tools/run_camera_tool.py` - Menu-driven access to all tools

## 🎯 The Foundation Rule

**RULE**: Every session, every deployment, every feature addition starts with:
```bash
cd camera_tools/tests && python3 quick_camera_test.py
```

**If camera health fails:**
1. 🛑 **STOP** - Do not proceed
2. 🔧 **FIX** - Address camera issues first  
3. ✅ **VERIFY** - Re-run foundation test
4. ▶️ **PROCEED** - Only after foundation is solid

## 🔧 Troubleshooting (Bottom-Up)

### Camera Health Test Fails
```bash
# Run diagnostics
cd camera_tools/diagnostics
python3 camera_diagnostics.py

# Check permissions  
python3 check_camera_permissions.py

# Fix issues and re-test foundation
cd ../tests
python3 quick_camera_test.py
```

### Higher Layer Fails
1. **First**: Re-run foundation test
2. **Second**: Check layer directly below
3. **Third**: Debug specific layer
4. **Always**: Work bottom-up

## 🏆 Success Criteria

### ✅ Foundation Solid
```
✅ Camera 0: HEALTHY and ACTIVE
✅ Frame capture: 90%+ success rate  
✅ Resolution: 640x480 confirmed
✅ Test frames: Saved successfully
```

### ✅ Each Layer Builds Successfully
- Health monitoring shows real metrics
- Live dashboard streams video
- Advanced features process frames
- No resource conflicts

## 📞 Support

### Foundation Issues
- Camera not detected → Check hardware/drivers
- Permissions denied → Run `check_camera_permissions.py`
- Black frames → Check lighting/lens cover
- Low success rate → Hardware malfunction

### Integration Issues
- Always start with foundation test
- Work layer by layer upward
- Each layer must pass before next

---

## 🎯 Available Dashboards

### 📹 Basic Camera Dashboard
- **URL**: http://localhost:5002
- **Features**: Live video streaming, camera health monitoring
- **Purpose**: Foundation verification and basic monitoring

### 📊 Basic Fatigue Detection
- **URL**: http://localhost:5001  
- **Features**: Progressive PERCLOS simulation, motion detection, alert levels
- **Purpose**: Fatigue monitoring without external dependencies

### 🧠 Advanced Fatigue Detection
- **URL**: http://localhost:5000
- **Features**: MediaPipe face tracking, real blink detection, eye landmark analysis
- **Purpose**: Production-grade fatigue detection (requires MediaPipe)

---

**🎯 Remember: Strong foundations create reliable systems. Always test camera health first.**

[![Camera Health](https://img.shields.io/badge/Foundation-Camera%20Health%20First-critical)](camera_tools/tests/)
[![Test Driven](https://img.shields.io/badge/Architecture-Test%20Driven-blue)](camera_tools/)
[![Fatigue Detection](https://img.shields.io/badge/Feature-Fatigue%20Detection-orange)](basic_fatigue_dashboard.py)

## Zoom RTMS Ingestion

A standalone Node service under `rtms-service/` listens for Zoom RTMS webhooks and stores audio/video/transcript artifacts in S3. Run it alongside the Flask app:

```bash
cd rtms-service
npm install
npm start
```

Configure the Zoom OAuth credentials (`ZM_RTMS_CLIENT`, `ZM_RTMS_SECRET`) and S3 environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET`), then point the Zoom webhook at `/rtms/webhook` on this service.  To have chunks recorded in
the Phase-2 capture database, set `CAPTURE_API_BASE_URL` (typically `https://<app>/api/rtms`) and the
matching `CAPTURE_API_TOKEN` so the service can call the new ingestion endpoints.
