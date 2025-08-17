# Start a Streaming Session - Behavioral Signals API Documentation

## Overview
The Behavioral Signals API offers real-time emotion & behavior recognition and deepfake detection through a streaming endpoint.

## Starting a Stream via UI
> The UI provides a simple way to try out the streaming endpoint. For production use, recommend using SDK or gRPC client.

### Steps:
1. From Projects page, select Project
2. Click "Stream From Mic"
3. Allow microphone access
4. Click "Start Streaming"
5. Speak
6. View real-time results

## Starting a Stream using Python SDK

### Code Example
```python
from behavioralsignals import Client, StreamingOptions
from behavioralsignals.utils import make_audio_stream

cid = "<your-cid>"
token = "<your-api-token>"
file_path = "/path/to/audio.wav"

client = Client(cid, token)
audio_stream, sample_rate = make_audio_stream(file_path, chunk_size=250)
options = StreamingOptions(sample_rate=sample_rate, encoding="LINEAR_PCM")

for result in client.behavioral.stream_audio(audio_stream=audio_stream, options=options):
    print(result)
```

### Key Points:
- Uses `make_audio_stream` to transform audio file into chunks
- Supports any `Iterator[bytes]` input
- Currently only supports Linear PCM encoding
- Returns `StreamingResultResponse` objects

## Next Steps
- Explore Behavioral Signals Python SDK
- Review Streaming API Functionality
- Learn about Real-time Deepfake Detection