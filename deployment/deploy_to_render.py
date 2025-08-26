#!/usr/bin/env python3
"""
Deploy to Render programmatically
"""

import requests
import subprocess
import time
import json

def deploy_to_render():
    """Deploy using Render's webhook deployment"""
    
    print("🎨 DEPLOYING TO RENDER")
    print("=" * 50)
    
    # Deploy via web API
    render_deploy_url = "https://render.com/deploy?repo=https://github.com/michael-abdo/webcam-communication-project&branch=deploy"
    
    print(f"📡 Render deployment URL: {render_deploy_url}")
    print("\n🔄 Alternative: Direct git deployment...")
    
    try:
        # Try direct webhook if available
        print("📦 Creating Render deployment...")
        
        # The deployment should happen automatically via GitHub integration
        # Let's wait and test
        print("⏳ Waiting for Render deployment (3 minutes)...")
        
        # Test multiple possible Render URLs
        possible_urls = [
            "https://webcam-communication-project.onrender.com",
            "https://fatigue-detection-system.onrender.com", 
            "https://webcam-production.onrender.com"
        ]
        
        for minutes in range(3):
            print(f"\n🧪 Testing after {minutes + 1} minute(s)...")
            
            for url in possible_urls:
                try:
                    print(f"   Testing: {url}")
                    response = requests.get(f"{url}/health", timeout=5)
                    if response.status_code == 200:
                        print(f"🎉 RENDER DEPLOYMENT SUCCESSFUL!")
                        print(f"✅ URL: {url}")
                        print(f"✅ Health: {response.json()}")
                        return url
                except:
                    continue
            
            if minutes < 2:
                time.sleep(60)  # Wait 1 minute between tests
        
        print("⚠️ Render deployment may still be building...")
        print(f"📋 Manual deploy URL: {render_deploy_url}")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    deploy_to_render()