# Check the Progress of a Process

## Overview
This documentation explains how to check the status of a processing job using the Behavioral Signals API.

## Status Values
- `0`: Pending (audio submitted for processing)
- `1`: Processing started
- `2`: Processing complete
- `-1, -3`: Server error
- `-2`: Insufficient credits

## Request Methods

### cURL Example
```shell
curl --location 'https://api.behavioralsignals.com/v5/clients/<your-project-id>/processes/<pid>' \
--header 'X-Auth-Token: your-api-token'
```

### Python SDK Example
```python
from behavioralsignals import Client
cid = "<your-cid>"
token = "<your-api-token>"
pid = <your-pid>

client = Client(cid, token)
output = client.behavioral.get_process(pid=pid)
```

## Response Example
```json
{
   "pid": 1,
   "cid": "<your-project-id>",
   "name": "my-awesome-audio",
   "status": 2,
   "statusmsg": "Processing Complete.",
   "duration": 5.03,
   "datetime": "2024-07-19T12:08:32.507Z",
   "meta": ""
}
```

## Next Steps
After checking the process status, you can [get results after completion](/docs/get-results-after-completion).