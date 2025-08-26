#!/usr/bin/env python3
"""
Direct Railway Deployment
Using GitHub integration method
"""

import webbrowser
import time

def deploy_to_railway():
    """Deploy directly to Railway using GitHub integration"""
    
    print("🚂 DEPLOYING TO RAILWAY.APP")
    print("=" * 50)
    print()
    print("Opening Railway's GitHub deployment page...")
    print()
    
    # Direct Railway GitHub deployment URL
    railway_url = "https://railway.app/new/github"
    
    # Open Railway deployment page
    webbrowser.open(railway_url)
    
    print("📋 MANUAL STEPS IN RAILWAY:")
    print()
    print("1. Click 'Login with GitHub' if not already logged in")
    print("2. Click 'Deploy from GitHub repo'")
    print("3. Search for: mh2010github/webcam")
    print("4. Select the repository when it appears")
    print("5. Choose branch: deploy")
    print("6. Click 'Deploy Now'")
    print()
    print("⏱️  Deployment will take 2-3 minutes")
    print()
    print("✅ After deployment completes:")
    print("   - Click on your service in Railway dashboard")
    print("   - Find 'Settings' tab")
    print("   - Look for your deployment URL")
    print("   - It will be: https://[app-name].railway.app")
    print()
    print("🧪 Test your deployment:")
    print("   curl https://[your-app].railway.app/health")
    print("   curl https://[your-app].railway.app/api/info")
    print()
    
    # Alternative: Direct repository link
    time.sleep(2)
    print("🔗 Alternative: Direct repository deployment")
    direct_repo_url = "https://railway.app/new/github/mh2010github/webcam?branch=deploy"
    print(f"   URL: {direct_repo_url}")
    print("   Opening this URL as backup option...")
    
    # Open direct repository URL
    webbrowser.open(direct_repo_url)

if __name__ == "__main__":
    deploy_to_railway()