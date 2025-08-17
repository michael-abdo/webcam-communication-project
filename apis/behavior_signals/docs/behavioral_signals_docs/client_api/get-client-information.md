# Get Client Information

This documentation explains how to retrieve client information using the Behavioral Signals API.

## Overview
You can get project (client) information associated with a specific client ID (cid) at any time.

## API Endpoint
`GET https://api.behavioralsignals.com/clients/cid`

## Authentication
Requires an authentication token (`x-auth-token`)

## Request Examples

### cURL
```curl
curl --request GET \
   --url https://api.behavioralsignals.com/clients/cid \
   --header 'accept: application/json' \
   --header 'x-auth-token: your_token'
```

### Python
```python
import requests

url = "https://api.behavioralsignals.com/clients/cid"
headers = {
    'accept': "application/json",
    'x-auth-token': "your_token"
}
response = requests.request("GET", url, headers=headers)
print(response.text)
```

### JavaScript
```javascript
var data = null;
var xhr = new XMLHttpRequest();
xhr.addEventListener("readystatechange", function () {
  if (this.readyState === this.DONE) {
    console.log(this.responseText);
  }
});
xhr.open("GET", "https://api.behavioralsignals.com/clients/cid");
xhr.setRequestHeader("accept", "application/json");
xhr.send(data);
```

## Example Response
```json
{
  "cid": "1234567890",
  "name": "my-awesome-project"
}
```

## Next Steps
- [Start a new process](/docs/first-steps)