# Create a Project and API Token

## Overview
This guide helps users create a Project to use the Behavioral Signals API. Users can create multiple Projects, each with a unique API Token for sending audio data.

## Steps to Create a Project

### Step 1: Login to Portal Console
- Visit [https://portal.behavioralsignals.com](https://portal.behavioralsignals.com)
- Log in with credentials

### Step 2: Create New Project
- Navigate to "Projects" page
- Click "ADD NEW PROJECT" button
- Provide a name and optional description
- Click "CREATE PROJECT"

### Step 3: Inspect Project Details
- Note the Project ID (client_id/cid)
- Retrieve the API Token (Secret)
- Keep API Token confidential

## API Modes

### Batch API (Asynchronous)
- Analyze pre-recorded audio files (.wav/.mp3)
- Submit audio for processing
- Check processing status
- Retrieve final prediction results

### Streaming API (Real-Time)
- Process audio in real-time
- Send live audio chunks
- Receive immediate prediction results
- Supports Behavioral and Deepfake tasks

> **Important**: Version 5.0.0 introduced significant schema changes. Existing projects are not compatible with new audio data.

## Next Steps
- [Start a new process](/docs/first-steps)
- [Start a streaming session](/docs/start-a-streaming-session)