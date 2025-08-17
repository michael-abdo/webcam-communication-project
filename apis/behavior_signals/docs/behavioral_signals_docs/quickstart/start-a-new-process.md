# Start a New Process - Behavioral Signals API Documentation

## Overview
This documentation explains how to start a new process for submitting audio files to the Behavioral Signals API. There are three primary methods:

### 1. Submit Audio Using UI
- Navigate to Projects page
- Click "UPLOAD AUDIO"
- Select audio file
- Click "START PROCESSING"

### 2. Submit Audio Using API
Example cURL request:
```shell
curl --location 'https://api.behavioralsignals.com/v5/clients/<your-project-id>/processes/audio' \
--header 'X-Auth-Token: your-api-token' \
--form 'file=@"/path/to/your/file.wav"' \
--form 'name="my-awesome-audio"'
```

### 3. Submit Audio Using Python SDK
```python
from behavioralsignals import Client

cid = "<your-cid>"
token = "<your-api-token>"
file_path = "/path/to/audio.wav"

client = Client(cid, token)
response = client.behavioral.upload_audio(file_path=file_path)
```

## Prerequisites
- Register with Behavioral Signals
- Create a Project
- Obtain Project ID (cid)
- Get API Token

## Response Details
Successful submission returns a JSON response with:
- `pid`: Unique process identifier
- `cid`: Project ID
- `name`: Audio file name
- `status`: Processing status
- `statusmsg`: Current status message
- `datetime`: Submission timestamp

## Next Steps
- [Check processing progress](/docs/check-the-processing-progress)