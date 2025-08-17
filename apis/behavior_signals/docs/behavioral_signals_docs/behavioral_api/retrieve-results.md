# Retrieve results

## Quickstart
- [Register to Behavioral Signals API](/docs/getting-started)
- [Create a Project and API Token](/docs/create-a-project-and-api-token)
- [Behavioral Signals Python SDK](/docs/behavioral-signals-python-sdk)
- [Start a new process](/docs/first-steps)
- [Check the progress of a process](/docs/check-the-processing-progress)
- [Get results after completion](/docs/get-results-after-completion)
- [Start a streaming session](/docs/start-a-streaming-session)

## Request

When a processing request is completed successfully, you can fetch the results. The results are provided in a JSON object format.

### Endpoint

```curl
curl --request GET \
     --url https://api.behavioralsignals.com/v5/clients/your-client-id/processes/pid/results \
     --header 'X-Auth-Token: your-api-token' \
     --header 'accept: application/json'
```

## Response Schema

The response is a JSON with the following structure:

```json
{
   "pid": 0,
   "cid": 0,
   "code": 0,
   "message": "string",
   "results": [
     {
       "id": "0",
       "startTime": "0.209",
       "endTime": "7.681",
       "task": "<task>",
       "prediction": [
         {
           "label": "<label_1>",
           "posterior": "0.9576"
         },
         {
           "label": "<label_2>",
           "posterior": "0.0377"
         }
       ],
       "finalLabel": "<label_1>",
       "level": "utterance"
     }
   ]
}
```

### Available Tasks

- **diarization**: Speaker label
- **asr**: Verbal content
- **gender**: Speaker's sex
- **age**: Speaker's age estimation
- **language**: Detected language
- **emotion**: Detected emotion (happy, angry