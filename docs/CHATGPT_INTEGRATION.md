# 🤖 ChatGPT Integration Guide

## For ChatGPT Users

Once your Railway deployment is complete, share this with ChatGPT:

```
I have deployed a Fatigue Detection API at: https://[your-app].railway.app

API Endpoints:
1. GET /health - Check if system is running
2. GET /api/info - Get system information  
3. GET /api/metrics - Get current fatigue metrics
4. POST /api/analyze - Analyze fatigue level
   Body: {"perclos": 0.0-1.0, "confidence": 0.0-1.0}

Example usage:
- Check health: GET https://[your-app].railway.app/health
- Analyze moderate fatigue: POST https://[your-app].railway.app/api/analyze
  Body: {"perclos": 0.25, "confidence": 0.95}

The API uses CORS and returns JSON responses. No authentication required.
```

## Example ChatGPT Prompts

### 1. System Status Check
```
Can you check if my fatigue detection system is running? 
API: https://[your-app].railway.app
```

### 2. Fatigue Analysis
```
Can you analyze this fatigue data using my API at https://[your-app].railway.app?
PERCLOS: 0.35 (eyes closed 35% of time)
Confidence: 0.92
```

### 3. Get Current Metrics
```
What are the current metrics from my fatigue detection system?
API: https://[your-app].railway.app/api/metrics
```

## ChatGPT Code Interpreter Usage

If using Code Interpreter, ChatGPT can run:

```python
import requests
import json

# Your deployment URL
api_url = "https://[your-app].railway.app"

# Check health
health = requests.get(f"{api_url}/health")
print("Health Status:", health.json())

# Analyze fatigue
data = {"perclos": 0.25, "confidence": 0.95}
response = requests.post(f"{api_url}/api/analyze", json=data)
print("Fatigue Analysis:", response.json())
```

## API Response Examples

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-21T12:00:00.000Z",
  "fatigue_system_available": true
}
```

### Fatigue Analysis Response
```json
{
  "fatigue_level": "MODERATE",
  "risk_score": 0.65,
  "recommendations": [
    "Take a 10-minute break",
    "Ensure proper lighting",
    "Check posture and screen distance"
  ],
  "perclos": 0.25,
  "confidence": 0.95,
  "timestamp": "2024-01-21T12:00:00.000Z"
}
```

### Fatigue Levels
- **ALERT** (0.0 - 0.15): Normal, fully alert
- **LOW** (0.15 - 0.25): Mild fatigue signs
- **MODERATE** (0.25 - 0.40): Noticeable fatigue
- **HIGH** (0.40 - 0.60): Significant fatigue
- **CRITICAL** (0.60+): Severe fatigue, immediate rest needed

## Integration Benefits

1. **Real-time Analysis**: ChatGPT can analyze fatigue data instantly
2. **Recommendations**: Get AI-powered suggestions based on fatigue levels
3. **Monitoring**: Track fatigue patterns over time
4. **Alerts**: ChatGPT can notify when critical fatigue detected
5. **Reports**: Generate fatigue analysis reports

## Advanced Usage

### Continuous Monitoring
```
Monitor my fatigue levels every 5 minutes using the API at https://[your-app].railway.app
Alert me if fatigue level exceeds MODERATE.
```

### Daily Summary
```
Can you create a daily fatigue summary using my API?
Check metrics at: https://[your-app].railway.app/api/metrics
```

### Integration with Other Tools
ChatGPT can integrate this API with:
- Calendar apps (schedule breaks)
- Notification systems (send alerts)
- Health tracking apps
- Productivity tools

## Troubleshooting

### CORS Errors
- CORS is enabled by default
- All origins are allowed
- Headers include: Access-Control-Allow-Origin: *

### Connection Issues
- Ensure URL includes https://
- Check if deployment is active in Railway dashboard
- Free tier has no sleep mode

### Invalid Responses
- Ensure JSON body is properly formatted
- PERCLOS must be between 0.0 and 1.0
- Confidence must be between 0.0 and 1.0

## Security Notes

- No API key required (public endpoint)
- HTTPS enforced by Railway
- Rate limiting handled by platform
- Safe for ChatGPT agent access

## Quick Test

Ask ChatGPT:
```
Please test all endpoints of my fatigue detection API at https://[your-app].railway.app and summarize the results.
```