# 🚀 RTMS Quickstart

This simple app demonstrates integration with the [Zoom Realtime Media Streams SDK](https://www.npmjs.com/package/@zoom/rtms) for Node.js.

[![npm](https://img.shields.io/npm/v/@zoom/rtms)](https://www.npmjs.com/package/@zoom/rtms)
[![docs](https://img.shields.io/badge/docs-online-blue)](https://zoom.github.io/rtms/js/)

## 📋 Setup

The SDK is already included in package dependencies. Install other dependencies:

```bash
npm install
```

## ⚙️ Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Set your Zoom OAuth credentials:
```bash
ZM_RTMS_CLIENT=your_client_id
ZM_RTMS_SECRET=your_client_secret
```

Everything (web UI, WebSocket bridge, and webhook) runs on a single port.  
For local development the default is `PORT=5000`. Zoom webhooks should target
`http://localhost:5000/zoom-webhook` (or whatever you configure via `ZM_RTMS_PATH`).

## 🏃‍♂️ Running the App

Start the application:

```bash
npm run dev          # loads variables from .env (local development)
npm start            # production-style start, expects env vars from the OS
```

For webhook testing with ngrok:

```bash
ngrok http 5000
```

Use the generated ngrok URL as your Zoom webhook endpoint (append `/zoom-webhook`).  
Then, start a meeting to see your data!

When deploying to Heroku:

1. `git push heroku <branch>:main`
2. Set config vars (`PORT` managed by Heroku, but add `CLIENT_ID`, `CLIENT_SECRET`,
   `ZM_RTMS_CLIENT`, `ZM_RTMS_SECRET`, and optionally `ZM_RTMS_PATH`)
3. Point Zoom at `https://<app-name>.herokuapp.com/zoom-webhook`
4. Open the public UI at `https://<app-name>.herokuapp.com/`

## 🎯 Basic Usage

Here's how you can implement the SDK yourself. 

### Import the SDK

**ES Modules:**
```javascript
import rtms from "@zoom/rtms";
```

**CommonJS:**
```javascript
const rtms = require('@zoom/rtms').default;
```

### Two Usage Patterns

The SDK supports two approaches for connecting to meetings:

#### 1. 🏢 Client-Based Approach (Multiple Meetings)

Use this for handling multiple concurrent meetings:

```javascript
// Create clients for each meeting
const client = new rtms.Client();

// Set up callbacks
client.onAudioData((buffer, size, timestamp, metadata) => {
  console.log(`🎵 Audio from ${metadata.userName}: ${size} bytes`);
});

client.onVideoData((buffer, size, timestamp, metadata) => {
  console.log(`📹 Video from ${metadata.userName}: ${size} bytes`);
});

client.onTranscriptData((buffer, size, timestamp, metadata) => {
  const text = buffer.toString('utf8');
  console.log(`💬 ${metadata.userName}: ${text}`);
});

// Join the meeting
client.join({
  meeting_uuid: "meeting-uuid",
  rtms_stream_id: "stream-id", 
  server_urls: "wss://rtms.zoom.us"
});
```

#### 2. 🌐 Global Singleton Approach (Single Meeting)

Use this for simple single-meeting applications:

```javascript
// Set up global callbacks
rtms.onAudioData((buffer, size, timestamp, metadata) => {
  console.log(`🎵 Audio from ${metadata.userName}: ${size} bytes`);
});

rtms.onTranscriptData((buffer, size, timestamp, metadata) => {
  const text = buffer.toString('utf8');
  console.log(`💬 ${metadata.userName}: ${text}`);
});

// Join the meeting
rtms.join({
  meeting_uuid: "meeting-uuid",
  rtms_stream_id: "stream-id",
  server_urls: "wss://rtms.zoom.us"
});
```

## 🪝 Webhook Integration

Set up webhook handling to automatically connect when meetings start:

```javascript
// Listen for Zoom webhook events
rtms.onWebhookEvent(({ event, payload }) => {
  if (event === "meeting.rtms_started") {
    const client = new rtms.Client();
    
    // Configure callbacks
    client.onAudioData((buffer, size, timestamp, metadata) => {
      // Process audio data
    });
    
    // Join using webhook payload
    client.join(payload);
  }
});
```

## 📊 Media Parameter Configuration

Configure audio, video, and deskshare processing parameters before joining:

### 🎵 Audio Parameters

```javascript
client.setAudioParams({
  contentType: rtms.AudioContentType.RAW_AUDIO,
  codec: rtms.AudioCodec.OPUS,
  sampleRate: rtms.AudioSampleRate.SR_16K,
  channel: rtms.AudioChannel.STEREO,
  dataOpt: rtms.AudioDataOption.AUDIO_MIXED_STREAM,
  duration: 20,     // 20ms frames
  frameSize: 640    // 16kHz * 2 channels * 20ms
});
```

### 📹 Video Parameters

```javascript
client.setVideoParams({
  contentType: rtms.VideoContentType.RAW_VIDEO,
  codec: rtms.VideoCodec.H264,
  resolution: rtms.VideoResolution.HD,
  dataOpt: rtms.VideoDataOption.VIDEO_SINGLE_ACTIVE_STREAM,
  fps: 30
});
```

### 🖥️ Deskshare Parameters

```javascript
client.setDeskshareParams({
  contentType: rtms.VideoContentType.RAW_VIDEO,
  codec: rtms.VideoCodec.H264,
  resolution: rtms.VideoResolution.FHD,
  dataOpt: rtms.VideoDataOption.VIDEO_SINGLE_ACTIVE_STREAM,
  fps: 15
});
```

## 📞 Available Callbacks

- `onJoinConfirm(reason)` - ✅ Join confirmation
- `onSessionUpdate(op, sessionInfo)` - 🔄 Session state changes  
- `onUserUpdate(op, participantInfo)` - 👥 Participant join/leave
- `onAudioData(buffer, size, timestamp, metadata)` - 🎵 Audio data
- `onVideoData(buffer, size, timestamp, metadata)` - 📹 Video data
- `onTranscriptData(buffer, size, timestamp, metadata)` - 💬 Live transcription
- `onLeave(reason)` - 👋 Meeting ended

## 📚 API Reference

For complete parameter options and detailed documentation:

- 🎵 **[Audio Parameters](https://zoom.github.io/rtms/js/interfaces/AudioParameters.html)** - Complete audio configuration options
- 📹 **[Video Parameters](https://zoom.github.io/rtms/js/interfaces/VideoParameters.html)** - Complete video configuration options  
- 🖥️ **[Deskshare Parameters](https://zoom.github.io/rtms/js/interfaces/VideoParameters.html)** - Complete deskshare configuration options
- 📖 **[Full API Documentation](https://zoom.github.io/rtms/js/)** - Complete SDK reference
