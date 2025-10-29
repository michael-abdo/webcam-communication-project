# RTMS Service

Zoom Realtime Media Streams (RTMS) ingestion service for Phase-2. Receives Zoom webhook events, joins the RTMS stream using the Zoom SDK, and saves audio/video/transcript payloads to S3.

## Configuration

Set the following environment variables (align with the Python app):

| Variable | Description |
| --- | --- |
| `ZM_RTMS_CLIENT` | Zoom OAuth client ID |
| `ZM_RTMS_SECRET` | Zoom OAuth client secret |
| `RTMS_WEBHOOK_PATH` | Path where the service listens for webhook events (default `/rtms/webhook`) |
| `S3_BUCKET` | Target S3 bucket |
| `AWS_REGION` | AWS region (default `us-west-2`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS credentials with write access to the bucket |
| `RTMS_SERVICE_PORT` | Port for this service (defaults to `$PORT` or `8080`) |
| `CAPTURE_API_BASE_URL` | Base URL of the Phase-2 capture API (e.g. `https://app.example.com/api/rtms`) |
| `CAPTURE_API_TOKEN` | Optional bearer token matching `CAPTURE_API_TOKEN` in Phase-2 |

AWS credentials are read from the usual environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

## Running locally

```bash
cd rtms-service
npm install
npm start

Open http://localhost:8080/rtms/ui to view the live RTMS dashboard (WebSocket stream and
auto-play audio/video). The same process also exposes `/rtms/webhook` for Zoom events.
```

Expose the webhook (e.g. with `ngrok http 8080`) and register the public URL with Zoom.
If you want captured media indexed in the Phase-2 database, set `CAPTURE_API_BASE_URL` to the
application's `/api/rtms` endpoint and provide the same `CAPTURE_API_TOKEN` the Flask app uses.

## Deployment

Add a process entry (e.g. `rtms: node rtms-service/index.js`) to the platform’s Procfile or supervisor config, ensure the environment variables above are present, and configure the Zoom app to hit `<app-url>/rtms/webhook`.
