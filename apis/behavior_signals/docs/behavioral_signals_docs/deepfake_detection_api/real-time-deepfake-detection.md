# Real-time Deepfake Detection

## Overview

The Behavioral Signals Streaming API supports real-time audio deepfake detection with two primary detection modes:

### Detection Levels

1. **Segment Level**
   - Results streamed every 2 seconds
   - Shorter time windows
   - Potentially less accurate predictions

2. **Utterance Level**
   - Results streamed at end of each utterance
   - Whole utterance analyzed
   - More accurate predictions

### Key Requirements

- 16kHz mono audio
- Linear PCM signed 16-bit encoding
- Chunk duration recommended between 100ms-500ms
- Voice activity detection precedes analysis

## Implementation Methods

### 1. Bare gRPC Client (Java Example)

Prerequisites:
- Java
- Maven
- Project CID and API token

Example Java streaming implementation included in documentation.

### 2. Python SDK Method

```python
from behavioralsignals import Client, StreamingOptions
from behavioralsignals.utils import make_audio_stream

cid = "<your-cid>"
token = "<your-api-token>"
file_path = "/path/to/audio.wav"

client = Client(cid, token)
audio_stream, sample_rate = make_audio_stream(file_path, chunk_size=250)
options = StreamingOptions(sample_rate=sample_rate, encoding="LINEAR_PCM")

for result in client.deepfakes.stream_audio(audio_stream=audio_stream, options=options):
    print(result)
```

### Result Retrieval

Past stream results can be retrieved using the get results endpoint or SDK with the corresponding process ID (pid).