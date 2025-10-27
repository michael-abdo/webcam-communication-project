#!/bin/bash

# Deploy WebSocket fix to Heroku

echo "Deploying WebSocket fix to Heroku..."

# Ensure we're in the phase-2 directory
cd "$(dirname "$0")"

# Add and commit the changes
git add Procfile requirements.txt requirements_lightweight.txt
git commit -m "Fix WebSocket connection issue - remove gevent-websocket conflict"

# Push to Heroku
git push heroku main

echo "Deployment complete!"
echo "Monitor the logs with: heroku logs --tail"