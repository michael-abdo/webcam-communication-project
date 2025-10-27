# S3 Streaming Fix Action Plan

> **Note:** As of 2025-07 the system no longer uses `/api/presigned-url`; uploads flow through `/api/sessions/<id>/chunks` via multipart form submissions handled server-side.

## Quick Fix (Restore Working S3)

### Step 1: Backup Current Changes
```bash
# Create a backup branch
git checkout -b backup-test-integration-2128157
git add .
git commit -m "Backup: Test integration changes before S3 fix"
```

### Step 2: Restore Working S3 Files
```bash
# Restore the working stream recorder
git checkout eee43f6 -- static/js/stream_recorder.js

# Create a backup of current app_lightweight.py
cp app_lightweight.py app_lightweight_with_tests.py
```

### Step 3: Extract Pure S3 Endpoint
Create a new file `streaming/s3_endpoints.py`:
```python
from flask import jsonify, request
from streaming.s3_handler import generate_presigned_post

def get_pure_presigned_url():
    """Generate presigned URL for direct S3 upload - no test integration."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        chunk_number = data.get('chunk_number', 0)
        
        # Generate presigned POST URL
        presigned_data = generate_presigned_post(session_id, chunk_number)
        return jsonify(presigned_data)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to generate presigned URL'
        }), 500
```

### Step 4: Update app_lightweight.py
Add a pure S3 endpoint alongside the test-integrated one:
```python
# Pure S3 streaming endpoint
@app.route('/api/s3/presigned-url', methods=['POST'])
def pure_s3_presigned_url():
    from streaming.s3_endpoints import get_pure_presigned_url
    return get_pure_presigned_url()
```

### Step 5: Update Frontend to Use Pure Endpoint
In `stream_recorder.js`, update the endpoint:
```javascript
// Change from:
const response = await fetch('/api/presigned-url', {

// To:
const response = await fetch('/api/s3/presigned-url', {
```

## Proper Integration (Long-term Solution)

### Architecture Separation
```
┌─────────────────────┐     ┌────────────────────┐
│   Pure S3 Stream    │     │  Test Integration  │
├─────────────────────┤     ├────────────────────┤
│ /api/s3/presigned   │     │ /api/test/record   │
│ Simple & Stateless  │     │ Session Tracking   │
│ No Dependencies     │     │ Test Correlation   │
└─────────────────────┘     └────────────────────┘
         │                           │
         └───────────┬───────────────┘
                     │
              ┌──────┴──────┐
              │ S3 Handler  │
              │  (Shared)   │
              └─────────────┘
```

### Implementation Steps

1. **Create Separate Test Recording Component**
   ```javascript
   // test_stream_recorder.js
   class TestStreamRecorder extends StreamRecorder {
       constructor(testSessionId) {
           super();
           this.testSessionId = testSessionId;
       }
       
       async getPresignedUrl(chunkNumber) {
           // Use test-integrated endpoint
           return await fetch('/api/presigned-url', {
               // Include test session data
           });
       }
   }
   ```

2. **Maintain Two Endpoints**
   - `/api/s3/presigned-url` - Pure S3 uploads
   - `/api/presigned-url` - Test-integrated uploads

3. **Update Templates**
   - `stream.html` - Uses pure S3 endpoint
   - `test_session_combined.html` - Uses test-integrated endpoint

## Verification Steps

1. **Test Pure S3 Streaming**
   ```bash
   # Start the server
   python app_lightweight.py
   
   # Navigate to /stream
   # Start recording and verify chunks upload to S3
   ```

2. **Verify S3 Bucket**
   ```bash
   # Check AWS S3 console or use AWS CLI
   aws s3 ls s3://xendoex-webcam-streaming-2025/ --recursive
   ```

3. **Monitor Browser Console**
   - Should see successful 204 responses from S3
   - No CORS errors
   - Chunks uploading every 5 seconds

## Rollback Plan

If issues persist:
```bash
# Full rollback to working state
git checkout eee43f6 -- static/js/stream_recorder.js app_lightweight.py

# Or cherry-pick specific S3 fixes
git log --oneline eee43f6..HEAD | grep -i "s3\|fix"
```

## Success Criteria

✅ S3 uploads work without test session data
✅ Original `/stream` page records and uploads successfully  
✅ Test integration remains functional on separate endpoints
✅ No state pollution between systems
✅ Clean separation of concerns
