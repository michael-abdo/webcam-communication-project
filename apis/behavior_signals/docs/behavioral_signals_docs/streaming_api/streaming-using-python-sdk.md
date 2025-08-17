# Streaming using the Python SDK

## Installation
```shell
pip install behavioralsignals
```

## Code Example
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

## Key Details
- The `client.behavioral.stream_audio` method requires an `Iterator[bytes]` for audio streaming
- `StreamingOptions` define the sample rate and encoding of the audio stream

## Additional Resources
- Check streaming examples for microphone and file streaming in the [GitHub repository](https://github.com/BehavioralSignalTechnologies/behavioralsignals-python/tree/main/examples/streaming)

*Updated 1 day ago*