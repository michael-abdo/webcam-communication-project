#!/usr/bin/env python3
"""
Automated Deployment Script
Opens Render deployment URL directly
"""

import webbrowser
import time

def deploy_to_render():
    """Deploy to Render with one click"""
    
    print("🚀 DEPLOYING FATIGUE DETECTION SYSTEM TO RENDER")
    print("=" * 50)
    print()
    print("This will:")
    print("✅ Deploy your app with automatic HTTPS")
    print("✅ Configure CORS for ChatGPT compatibility")
    print("✅ Set up free hosting (spins down after 15 min)")
    print("✅ Use the deploy branch from GitHub")
    print()
    
    # Render deployment URL with your repository
    render_url = "https://render.com/deploy?repo=https://github.com/mh2010github/webcam&branch=deploy"
    
    print("Opening Render deployment page...")
    print(f"URL: {render_url}")
    print()
    
    # Open the deployment URL
    webbrowser.open(render_url)
    
    print("📋 NEXT STEPS:")
    print("1. Click 'Connect GitHub' if not already connected")
    print("2. Authorize Render to access your repository")
    print("3. Review the deployment settings (already configured)")
    print("4. Click 'Create Web Service'")
    print("5. Wait 3-5 minutes for deployment to complete")
    print()
    print("🔗 After deployment, your app will be available at:")
    print("   https://[your-app-name].onrender.com")
    print()
    print("📝 Example endpoints to test:")
    print("   https://[your-app-name].onrender.com/health")
    print("   https://[your-app-name].onrender.com/api/info")
    print()
    
    # Also provide Railway option
    print("🚂 Alternative: Deploy to Railway")
    print("   URL: https://railway.app/new/github")
    print("   - Select mh2010github/webcam repository")
    print("   - Choose deploy branch")
    print()

if __name__ == "__main__":
    deploy_to_render()