# 🚁 Fly.io Backup Deployment

## Why Fly.io as Backup?

- **Generous free tier**: 3 shared-cpu VMs, 3GB persistent storage
- **Global edge network**: Deploy close to users
- **Automatic HTTPS**: Like Railway and Render
- **Zero cold starts**: Machines stay warm

## Prerequisites

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Sign up and login:
```bash
fly auth signup
# or if you have an account:
fly auth login
```

## Deployment Steps

### 1. Initialize Fly App

```bash
# In your project directory
fly launch --no-deploy

# When prompted:
# - App name: fatigue-detection-[unique]
# - Region: Choose closest to you
# - Postgres: No
# - Redis: No
```

### 2. Deploy

```bash
# Deploy from deploy branch
git checkout deploy
fly deploy
```

### 3. Get Your URL

```bash
fly status
# Look for: https://[app-name].fly.dev
```

### 4. Test Deployment

```bash
# Health check
curl https://[app-name].fly.dev/health

# Validate all endpoints
python3 validate_live_deployment.py https://[app-name].fly.dev
```

## Fly.io Advantages

1. **Better Performance**: Runs on Firecracker VMs
2. **Auto-scaling**: Scales to zero, auto-starts on request
3. **Multi-region**: Easy to deploy globally
4. **WebSockets**: Full support (if needed later)

## Monitoring

```bash
# View logs
fly logs

# Check status
fly status

# Monitor metrics
fly dashboard
```

## Configuration Notes

The `fly.toml` file is pre-configured with:
- Force HTTPS enabled
- Health checks on /health endpoint
- Auto stop/start for cost efficiency
- Proper port configuration

## Troubleshooting

### App Won't Start
```bash
fly logs
# Check for missing dependencies or port binding issues
```

### Slow Response Times
```bash
# Scale up if needed (uses paid tier)
fly scale count 2
```

### Domain Issues
```bash
# Add custom domain
fly certs add yourdomain.com
```

## Quick Commands

```bash
# Deploy
fly deploy

# Open app
fly open

# SSH into container
fly ssh console

# Restart
fly apps restart [app-name]

# Destroy (careful!)
fly apps destroy [app-name]
```

## Cost Notes

- **Free tier**: 3 small VMs (shared-cpu-1x with 256MB RAM)
- **Auto-stop**: Machines stop when idle (saves resources)
- **No credit card**: Required only for scaling beyond free tier

This provides a reliable backup to Railway and Render deployments!