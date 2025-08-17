# Behavioral Signals API Documentation Index

This directory contains the complete offline documentation for the Behavioral Signals API v5.2.0.

## Documentation Structure

### Getting Started
- [Getting Started](getting-started.md)

### Quickstart
- [Register to Behavioral Signals API](quickstart/create-a-project-and-api-token.md)
- [Create a Project and API Token](quickstart/create-a-project-and-api-token.md)
- [Behavioral Signals Python SDK](quickstart/behavioral-signals-python-sdk.md)
- [Start a new process](quickstart/start-a-new-process.md)
- [Check the processing progress](quickstart/check-the-processing-progress.md)
- [Get results after completion](quickstart/get-results-after-completion.md)
- [Start a streaming session](quickstart/start-a-streaming-session.md)

### Behavioral API
- [Submit audio file](behavioral_api/submit-audio-file.md)
- [Retrieve results](behavioral_api/retrieve-results.md)
- [Embeddings](behavioral_api/embeddings.md)

### Streaming API
- [Functionality and definitions](streaming_api/functionality-and-definitions.md)
- [Streaming using Python SDK](streaming_api/streaming-using-python-sdk.md)
- [Streaming using bare gRPC client](streaming_api/streaming-using-bare-grpc-client.md)
- [Proto file](streaming_api/proto-file.md)

### Deepfake Detection API
- [Definition of audio deepfakes](deepfake_detection_api/definition-of-audio-deepfakes.md)
- [Interactive demo](deepfake_detection_api/interactive-demo.md)
- [Submit an audio for processing](deepfake_detection_api/submit-an-audio-for-processing.md)
- [Real-time deepfake detection](deepfake_detection_api/real-time-deepfake-detection.md)

### Client API
- [Get client information](client_api/get-client-information.md)

### Status API
- [Get a status update of the service](status_api/get-a-status-update-of-the-service.md)

## Key Resources

- **Platform Registration**: https://platform.behavioralsignals.com
- **API Base URL**: https://api.behavioralsignals.com
- **Streaming Endpoint**: streaming.behavioralsignals.com:443
- **Python SDK GitHub**: https://github.com/BehavioralSignalTechnologies/behavioralsignals-python
- **Interactive Deepfake Demo**: https://detect.behavioralsignals.com

## API Version

This documentation covers Behavioral Signals API v5.2.0.

> **Note**: Version 5.0.0 introduced significant schema changes. Existing projects created before v5.0.0 are not compatible with new audio data.

## Quick Links

- Install Python SDK: `pip install behavioralsignals`
- Discord Community for support
- API requires authentication via Project ID (cid) and API Token