# Behavioral Signals Python SDK Documentation

## Overview
The Behavioral Signals Python SDK provides an easy way to integrate voice analysis and deepfake detection APIs into applications. It supports both batch and streaming audio input modes.

## Installation
Install via PyPI:
```shell
pip install behavioralsignals
```

## Simple Usage Example
```python
from behavioralsignals import Client

cid = "<your-cid>"
token = "<your-api-token>"
file_path = "/path/to/audio.wav"

client = Client(cid, token)
response = client.behavioral.upload_audio(file_path=file_path)
output = client.behavioral.get_result(pid=response.pid)
```

## Key Features
- Behavioral API for analyzing human behavior through voice
- Deepfakes API for detecting synthetic audio content
- Supports batch and streaming modes
- Real-time and post-processing result retrieval

## Additional Resources
- GitHub Repository: [https://github.com/BehavioralSignalTechnologies/behavioralsignals-python](https://github.com/BehavioralSignalTechnologies/behavioralsignals-python)
- Discord Server for support and community engagement

## Documentation Sections
- Quickstart
- Behavioral API
- Streaming API
- Deepfake Detection API
- Client API
- Status API

The SDK aims to simplify integration of voice analysis technologies into various applications like voice analytics, contact center tools, and media authentication.