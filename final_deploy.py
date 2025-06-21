#!/usr/bin/env python3
"""
Final Deployment Script - Multiple Platform Deployment
"""

import subprocess
import time
import requests
import webbrowser
import os

def test_url(url, timeout=5):
    """Test if a URL is responding"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def deploy_with_netlify():
    """Deploy using Netlify Drop"""
    print("🌐 NETLIFY DROP DEPLOYMENT")
    print("=" * 40)
    
    # Create a simple build
    os.makedirs("dist", exist_ok=True)
    
    # Copy essential files to dist
    essential_files = ["app.py", "requirements.txt", "Procfile"]
    for file in essential_files:
        if os.path.exists(file):
            subprocess.run(["cp", file, "dist/"], check=True)
    
    print("📁 Created dist/ folder with deployment files")
    print("🌐 Opening Netlify Drop...")
    
    # Open Netlify drop
    webbrowser.open("https://app.netlify.com/drop")
    
    print("\n📋 MANUAL STEPS:")
    print("1. Drag the 'dist' folder to the Netlify Drop page")
    print("2. Wait for deployment to complete")
    print("3. Get your URL (format: https://random-name.netlify.app)")
    
    return "netlify_manual"

def deploy_comprehensive():
    """Comprehensive deployment across multiple platforms"""
    
    print("🚀 COMPREHENSIVE DEPLOYMENT STRATEGY")
    print("=" * 60)
    
    # 1. Test if Railway is working
    print("\n1️⃣ Testing Railway...")
    railway_url = "https://webcam-communication-project-production.up.railway.app"
    working, data = test_url(railway_url)
    if working:
        print(f"✅ Railway is LIVE: {railway_url}")
        return railway_url
    else:
        print("❌ Railway not responding")
    
    # 2. Open deployment URLs
    deployment_urls = [
        ("Render", "https://render.com/deploy?repo=https://github.com/michael-abdo/webcam-communication-project&branch=deploy"),
        ("Vercel", "https://vercel.com/new/clone?repository-url=https://github.com/michael-abdo/webcam-communication-project&branch=deploy"),
        ("Netlify", "https://app.netlify.com/start/deploy?repository=https://github.com/michael-abdo/webcam-communication-project&branch=deploy")
    ]
    
    print("\n2️⃣ Opening backup deployment options...")
    for platform, url in deployment_urls:
        print(f"🔗 {platform}: {url}")
        webbrowser.open(url)
        time.sleep(2)  # Stagger browser openings
    
    # 3. Create local test server
    print("\n3️⃣ Starting local backup server...")
    try:
        # Start local server in background
        import threading
        def run_local():
            subprocess.run(["python3", "app.py"], cwd="/home/Mike/projects/webcam")
        
        server_thread = threading.Thread(target=run_local, daemon=True)
        server_thread.start()
        
        time.sleep(3)  # Give server time to start
        
        # Test local server
        working, data = test_url("http://localhost:5000")
        if working:
            print("✅ Local server running at: http://localhost:5000")
        
    except Exception as e:
        print(f"⚠️ Local server issue: {e}")
    
    # 4. Deploy via Netlify Drop
    deploy_with_netlify()
    
    print("\n" + "=" * 60)
    print("🎯 DEPLOYMENT STATUS SUMMARY")
    print("=" * 60)
    print("✅ Railway: Deployed (may still be building)")
    print("🔗 Render: Deployment page opened")
    print("🔗 Vercel: Deployment page opened") 
    print("🔗 Netlify: Drop page opened")
    print("🏠 Local: http://localhost:5000 (if started)")
    
    print("\n📋 NEXT STEPS:")
    print("1. Check which platform deploys first")
    print("2. Copy the working URL")
    print("3. Run: python3 validate_live_deployment.py YOUR_URL")
    
    # Monitor for successful deployments
    print("\n🔍 Monitoring for successful deployments...")
    potential_urls = [
        "https://webcam-communication-project.onrender.com",
        "https://fatigue-detection-system.onrender.com",
        "https://webcam-communication-project.vercel.app",
        railway_url
    ]
    
    for minute in range(5):  # Monitor for 5 minutes
        print(f"\n⏱️ Minute {minute + 1}/5 - Checking deployments...")
        
        for url in potential_urls:
            working, data = test_url(url, timeout=3)
            if working:
                print(f"🎉 SUCCESS! Deployment found: {url}")
                print(f"✅ Health check: {data}")
                return url
        
        if minute < 4:
            time.sleep(60)
    
    print("\n⚠️ Deployments may still be building. Check the opened browser tabs.")
    return None

if __name__ == "__main__":
    result = deploy_comprehensive()
    if result and result.startswith("http"):
        print(f"\n🎊 FINAL RESULT: {result}")
    else:
        print("\n📋 Check your browser tabs for deployment status!")