# Embeddings

## Introduction

Embeddings are numerical representations of data (vectors) that capture underlying patterns and relationships within input. In audio analysis, they serve two primary purposes:

1. **Speaker Embeddings**: 
   - 192-dimensional vector
   - Captures unique voice characteristics
   - Used for speaker identification/verification

2. **Behavioral Embeddings**:
   - 768-dimensional vector
   - Encapsulates behavioral speech characteristics
   - Includes emotion, positivity, and strength of utterance

## Common Use Cases

- Speaker recognition
- Customer service interaction analysis
- Media content indexing
- Advanced sentiment and engagement analytics

## How to Retrieve Embeddings from the API

To include embeddings in the response, set the `embeddings` query parameter to `true` when submitting an audio request:

```curl
curl --request POST \
     --url https://api.behavioralsignals.com/clients/your-client-id/processes/audio \
     --header 'X-Auth-Token: your-api-token' \
     --header 'accept: application/json' \
     --header 'content-type: multipart/form-data' \
     --form name=my-awesome-audio \
     --form embeddings=true \
     --form 'meta={"key": "value"}'
```

These embeddings transform complex audio signals into standardized vectors, enabling more efficient machine learning tasks like clustering, classification, and similarity measurement.