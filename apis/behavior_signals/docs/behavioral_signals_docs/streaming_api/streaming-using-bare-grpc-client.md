# Streaming using a bare gRPC client

## Quickstart
- [Register to Behavioral Signals API](/docs/getting-started)
- [Create a Project and API Token](/docs/create-a-project-and-api-token)
- [Behavioral Signals Python SDK](/docs/behavioral-signals-python-sdk)
- [Start a new process](/docs/first-steps)
- [Check the progress of a process](/docs/check-the-processing-progress)
- [Get results after completion](/docs/get-results-after-completion)
- [Start a streaming session](/docs/start-a-streaming-session)

## 1. Generating gRPC Client Code

### Prerequisites
```bash
pip install grpcio grpcio-tools pydub
```

### Generate Python Client
1. Create a `protos/` directory in your project
2. Create an `api.proto` file from the Protocol Buffer documentation
3. Run:
```bash
python -m grpc_tools.protoc \
     --proto_path=protos/ \
     --python_out=. \
     --grpc_python_out=. \
     protos/api.proto
```

This generates:
- `api_pb2.py` - Message classes
- `api_pb2_grpc.py` - Service stub classes

## 2. Service Endpoints

| Service | Method | Purpose |
|---------|--------|---------|
| BehavioralStreamingApi | StreamAudio | Real-time behavioral analysis |
| BehavioralStreamingApi | DeepfakeDetection | Real-time deepfake detection |

## 3. Message Protocol Conventions

> First Message Rule: The first `AudioStream` message must contain only the configuration, without any audio data.

```python
def requests():
    # First message: Configuration only (no audio!)
    yield pb.AudioStream(
        cid=your_cid,
        x_auth_token="your_api_key",
        config=pb.AudioConfig(
            encoding=pb.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=16000
        )