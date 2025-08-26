#!/usr/bin/env python3
"""
Force Railway Deployment via GitHub Push
"""

import subprocess
import time
import requests

def trigger_deployment():
    """Force deployment by pushing to trigger Railway"""
    
    print("🚀 FORCING RAILWAY DEPLOYMENT")
    print("=" * 50)
    
    # Create a deployment trigger commit
    print("📝 Creating deployment trigger...")
    with open("DEPLOY_TRIGGER.txt", "w") as f:
        f.write(f"Deployment triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("This file triggers Railway auto-deployment\n")
    
    # Add and commit
    print("📦 Committing trigger...")
    subprocess.run(["git", "add", "DEPLOY_TRIGGER.txt", ".github/workflows/deploy.yml"], check=True)
    subprocess.run([
        "git", "commit", "-m", 
        "🚀 FORCE DEPLOYMENT: Trigger Railway Auto-Deploy\n\n" +
        "Manual deployment trigger to ensure Railway picks up latest changes.\n" +
        "This commit forces Railway to redeploy with all fixes applied.\n\n" +
        "🤖 Generated with [Claude Code](https://claude.ai/code)\n\n" +
        "Co-Authored-By: Claude <noreply@anthropic.com>"
    ], check=True)
    
    # Push to trigger Railway
    print("🔄 Pushing to GitHub (triggers Railway)...")
    subprocess.run(["git", "push", "origin", "deploy"], check=True)
    
    print("\n✅ Deployment triggered!")
    print("Railway should now automatically deploy from GitHub")
    
    # Wait and test
    print("\n⏳ Waiting 60 seconds for deployment...")
    time.sleep(60)
    
    # Test deployment
    url = "https://webcam-communication-project-production.up.railway.app/health"
    print(f"\n🧪 Testing deployment at: {url}")
    
    for attempt in range(6):  # 6 attempts over 2 minutes
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print("🎉 DEPLOYMENT SUCCESSFUL!")
                print(f"✅ Health check passed: {response.json()}")
                return True
        except:
            pass
        
        print(f"⏳ Attempt {attempt + 1}/6 - Still deploying...")
        time.sleep(20)
    
    print("⚠️ Deployment may still be in progress - check Railway dashboard")
    return False

if __name__ == "__main__":
    trigger_deployment()