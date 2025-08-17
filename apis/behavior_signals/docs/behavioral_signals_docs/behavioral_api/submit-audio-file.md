# Submit Audio File Documentation

## Overview
This documentation explains how to submit an audio file to the Behavioral Signals API for processing.

## Key Details
- Endpoint: `/clients/{cid}/processes/audio`
- Supported Audio Formats: wav, mp3, and other non-proprietary audio encodings
- Required Parameters:
  - `cid`: Project ID
  - `X-Auth-Token`: API Token

## Query Parameters

| Parameter | Description |
|-----------|-------------|
| `name` | Description of the audio |
| `meta` | JSON string with additional user-defined information |
| `embeddings` | Boolean to select embedding return (true/false) |

## Example cURL Request
```curl
curl --request POST \
     --url https://api.behavioralsignals.com/v5/clients/your-client-id/processes/audio \
     --header 'X-Auth-Token: your-api-token' \
     --header 'accept: application/json' \
     --header 'content-type: multipart/form-data' \
     --form name=my-awesome-audio \
     --form embeddings=false \
     --form 'meta={"key": "value"}'
```

## Example Response
```json
{
   "pid": 1,
   "cid": "<your-client-id>",
   "name": "my-awesome-audio",
   "status": 0,
   "statusmsg": "Pending",
   "duration": 0,
   "datetime": "2024-07-19T11:54:37.900Z",
   "meta": "{\"key\": \"value\"}"
}
```

## Response Details
- On successful submission, returns a unique process ID
- Includes initial processing state and metadata
- If request fails, returns an error code

## Next Steps
- [Check the progress of a process](/docs/check-the-processing-progress)