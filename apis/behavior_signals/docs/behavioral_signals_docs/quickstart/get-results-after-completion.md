# Get results after completion

## 📄 Description of the results

The API provides advanced audio analysis capabilities, offering predictions and insights about spoken content, including:

- **Speaker Diarization**: Identifies utterances of different speakers
- **Automatic Speech Recognition (ASR)**: Transcribes spoken words
- **Language Identification**: Determines language used
- **Emotion Detection**: Analyzes emotional tone
- **Strength Detection**: Assesses speech strength levels
- **Gender and Age Prediction**
- **Positivity Analysis**
- **Speaking Rate**
- **Hesitation Detection**
- **Engagement Assessment**

> Note: Behavioral results are available for utterances longer than 2 seconds. Shorter utterances have limited analysis.

## Retrieving the results - using the UI

Users can download JSON results by clicking the **download** button after processing.

## Retrieving the results - using the API

API request to get results:

```shell
curl --location 'https://api.behavioralsignals.com/v5/clients/<your-project-id>/processes/<pid>/results' \
--header 'X-Auth-Token: <your-api-token>'
```

## Retrieving the results - using the SDK

Python SDK example:

```python
from behavioralsignals import Client

cid = "<your-cid>"
token = "<your-api-token>"
pid = "<your-process-id>"

client = Client(cid, token)
output = client.behavioral.get_result(pid=pid)
```

The documentation provides a comprehensive guide to retrieving and understanding audio analysis results using Behavioral Signals API.