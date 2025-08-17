# Get a Status Update of the Service

You can use this API to get status information about the service.

## API Endpoint
`GET https://api.behavioralsignals.com/status`

## Code Examples

### cURL
```bash
curl --request GET \
   --url https://api.behavioralsignals.com/status \
   --header 'accept: application/json'
```

### JavaScript
```javascript
var request = require("request");
var options = { 
  method: 'GET',
  url: 'https://api.behavioralsignals.com/status',
  headers: { 
    'x-auth-token': 'your_token', 
    accept: 'application/json' 
  } 
};
request(options, function (error, response, body) {
  if (error) throw new Error(error);
  console.log(body);
});
```

### Python
```python
import requests

url = "https://api.behavioralsignals.com/status"
headers = {
    'accept': "application/json",
    'x-auth-token': "your_token"
}
response = requests.request("GET", url, headers=headers)
print(response.text)
```

## Description
"You can get current health status of the service by calling this API."

## Next Steps
- [Get client information](/docs/get-client-information)