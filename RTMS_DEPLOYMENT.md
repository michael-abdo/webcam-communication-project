# Phase-2 RTMS Deployment Overview

- **Heroku App:** https://xcellerate-eq-4f2dd61b4bbd-57798fc61cb7.herokuapp.com/
- **Dashboard UI:** /rtms/ui
- **Websocket Endpoint:** /rtms/ws
- **Zoom Webhook:** /rtms/webhook
- **Procfile:** `web: uvicorn app_lightweight:asgi_app --host 0.0.0.0 --port $PORT`, `rtms: node rtms-service/index.js`
- **Local Environment:** `.env` (AWS, Zoom, capture token) synced with `heroku config:set $(cat .env | xargs)`

### Deployment Steps
1. `pip install -r requirements.txt`
2. `npm install --prefix rtms-service`
3. `git push heroku HEAD:main`

Use `/rtms/ui` to monitor live RTMS streams. Websocket traffic is handled by Uvicorn (ASGI) using Flask-Sock.
