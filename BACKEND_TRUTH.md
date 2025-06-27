# Backend Truth Documentation

## The Reality

This system has **NO backend analytics**. The backend (`app_lightweight.py`) is a simple data categorizer that:

1. **Receives** PERCLOS values from the frontend
2. **Categorizes** them using basic thresholds
3. **Returns** hardcoded responses

## What Actually Happens

### Frontend (Browser)
- Uses MediaPipe Face Mesh to detect face landmarks
- Calculates Eye Aspect Ratio (EAR) 
- Computes PERCLOS (Percentage of Eye Closure)
- Sends results to backend

### Backend (Server)
- `/api/analyze`: Takes PERCLOS, returns category based on thresholds
- `/api/analysis-result`: Stores whatever client sends, no validation
- No ML models, no computer vision, no calculations

## The Deception

The backend claims:
- `accuracy: '100%'` - Hardcoded lie
- `algorithm_version: '2.0'` - Doesn't exist
- `processing_time_ms: 15` - Fake metric

## Why You See 0.0%

When MediaPipe fails to detect a face, the frontend sends `perclos: 0.0`. The backend categorizes this as "ALERT" because `0.0 <= 0.15`. It has no ability to verify if this is real data or not.

## The Truth

- All real processing happens client-side
- Backend is a passthrough with thresholds
- No server-side fatigue detection exists
- Video datasets are mostly hardcoded mock data
- The system depends entirely on browser-based MediaPipe working correctly