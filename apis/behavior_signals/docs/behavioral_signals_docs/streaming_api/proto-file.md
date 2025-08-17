# Proto file

The document describes the `api.proto` file for Behavioral Signals' gRPC streaming API. Here's a markdown summary:

## Key Details
- **Location**: `streaming.behavioralsignals.com:443`
- **Purpose**: Defines gRPC service for streaming behavioral and deepfake detection

## Main Services
1. `BehavioralStreamingApi` with two primary methods:
   - `StreamAudio()`: Bi-directional streaming for behavioral and emotion results
   - `DeepfakeDetection()`: Bi-directional streaming for deepfake detection results

## Key Components
### Audio Configuration
- Supports `LINEAR_PCM` audio encoding
- Configurable sample rate
- Optional result levels:
  - Segment-level results
  - Utterance-level results

### Message Types
- `AudioStream`: Streaming request message
- `AudioConfig`: Audio configuration
- `StreamResult`: Results response
- `InferenceResult`: Analysis result
- `Prediction`: Individual prediction with confidence

## Code Example
```protobuf
syntax = "proto3";
package behavioral_api.grpc.v1;

service BehavioralStreamingApi {
  rpc StreamAudio(stream AudioStream) returns (stream StreamResult) {}
  rpc DeepfakeDetection(stream AudioStream) returns (stream StreamResult) {}
}
```

The proto file provides a comprehensive definition for real-time audio analysis and deepfake detection streaming.