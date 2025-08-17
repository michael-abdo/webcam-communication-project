# Functionality and definitions

## Basic terminology

The document provides essential technical concepts and parameters for using the Behavioral Signals streaming API.

## ✍️ Usage

The Streaming API is designed for:
- Sending audio chunks (e.g., from a microphone)
- Getting real-time results
- Use cases include:
  * Streaming live calls
  * Agentic AI applications with live voice processing

Implemented using `gRPC` for high efficiency.

## 🎚️ Audio Processing Levels

### Segment Level
- Fixed 2-second audio chunks processed independently
- Provides granular, time-aligned behavioral metrics
- Continuous stream of metrics
- Best for live dashboards and immediate feedback

### Utterance Level
- Complete speech units defined by silence/speaker changes
- Variable duration
- Context-aware analysis
- Better accuracy for conversational analysis

## 🗣️ Voice Activity Detection (VAD)
- Detects human speech in audio signals
- Distinguishes speech from non-speech
- Identifies conversation pause points

## ⚙️ Configuration Parameters

### sampling_rate (required)
- Audio samples per second
- All rates supported
- Resampled to 16kHz for models

### encoding (required)
- Audio format specification
- Supports LINEAR_PCM
- Requires:
  * Mono channel
  * Consistent bit depth

### level (optional)
Options:
- `segment`
- `utterance`
- Default: returns both levels

The document includes a detailed JSON example of the API response, demonstrating various predictive metrics like gender, age, emotion, and engagement.

## What's Next
- [Streaming using Python SDK](/docs/streaming-using-python-sdk)
- [Streaming using bare gRPC client](/docs/streaming-using-a-bare-grpc-client)