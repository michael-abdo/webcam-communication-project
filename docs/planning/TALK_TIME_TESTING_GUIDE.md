# Talk Time Analytics Testing Guide

## 🔍 Current Status

The talk time analytics feature has been deployed to production with all services running:
- ✅ Web service (Basic dyno)
- ✅ RTMS service (Basic dyno) 
- ✅ Analytics worker (Basic dyno)
- ✅ Redis (connected)
- ✅ PostgreSQL (analytics tables created)

However, the UI appears to be missing the analytics visualization components.

## 🧪 How to Test

### 1. Access the RTMS Dashboard
Navigate to: https://xcellerate-eq-4f2dd61b4bbd-57798fc61cb7.herokuapp.com/rtms/

### 2. Start a Stream
1. You should see the "Zoom RTMS Live Preview" page
2. Click the "Start Stream" button
3. Enter a meeting number when prompted

### 3. What Should Happen
When working correctly, you should see:
- A "Talk Time Analytics" section below the transcript
- Real-time bar charts showing each participant's talk time
- Participation equality score
- Visual indicators matching speaker colors from the transcript

### 4. Current Issue
The analytics section HTML exists but the JavaScript functionality may not be fully integrated. The analytics data is being collected by the worker service but may not be displayed in the UI.

## 📊 Backend Verification

To verify the backend is working:

1. **Check Worker Logs**:
```bash
heroku logs --dyno=worker -n 50 -a xcellerate-eq-4f2dd61b4bbd
```
Look for: "Subscribed to channels: ['rtms:events:audio', 'rtms:events:transcript']"

2. **Check Database**:
```bash
heroku pg:psql -a xcellerate-eq-4f2dd61b4bbd
SELECT * FROM analytics_metrics ORDER BY timestamp DESC LIMIT 10;
```

## 🔧 Debugging Steps

1. Open browser developer console
2. Check for WebSocket connection to the server
3. Look for any JavaScript errors
4. Monitor Network tab for analytics-related messages

## 📝 Notes

- The analytics worker is running and connected to Redis
- It's subscribed to audio and transcript events
- The database schema is created and ready
- The issue appears to be with the frontend display of analytics data