# Submit an Audio for Processing - Behavioral Signals API Documentation

## Overview
This documentation explains how to submit audio files for deepfake detection analysis using two methods:

## 1. REST API Method

### Submitting a Recording
- Endpoint: `https://api.behavioralsignals.com/v5/detection/clients/your-cid-here/processes/audio`
- Supports `.wav` and `.mp3` files

#### Example cURL Request:
```shell
curl --request POST \
     --url https://api.behavioralsignals.com/v5/detection/clients/<your-cid>/processes/audio \
     --header 'X-Auth-Token: <your-api-token>' \
     --header 'accept: application/json' \
     --header 'content-type: multipart/form-data' \
     --form file='@/path/to/audio.wav'
```

### Retrieving Results
- Use the process ID from the initial submission
- Retrieve results via GET request to the API

## 2. Python SDK Method

### Submitting a Recording
```python
from behavioralsignals import Client
client = Client(YOUR_CID, YOUR_API_KEY)
response = client.deepfakes.upload_audio(file_path="audio.wav")
```

### Retrieving Results
```python
output = client.deepfakes.get_result(pid=<pid-of-process>)
```

## Result Details
- Results include multiple tasks:
  - ASR (Speech Recognition)
  - Diarization
  - Language Detection
  - Deepfake Detection

### Deepfake Detection Classes
- `bonafide`: Authentic audio
- `spoofed`: Deepfake audio

The results provide:
- Start and end times of utterances
- Prediction labels
- Posterior probabilities for each class

## Prerequisites
- Create a Project
- Obtain Client ID (CID)
- Generate API Token