#!/usr/bin/env python3
"""
One-Click Deployment Solution
Maximum automation for Fatigue Detection System deployment
"""

import webbrowser
import urllib.parse
import time

def create_deployment_urls():
    """Generate one-click deployment URLs for major platforms"""
    
    # Repository information
    repo_owner = "michael-abdo"
    repo_name = "webcam-communication-project"
    branch = "deploy"
    
    # Base repository URL
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    
    print("🚀 ONE-CLICK DEPLOYMENT GENERATOR")
    print("=" * 50)
    print()
    
    # Railway deployment URL
    railway_params = {
        'template': f'{repo_url}/tree/{branch}',
        'envs': '',
        'referralCode': ''
    }
    railway_url = "https://railway.app/new?" + urllib.parse.urlencode(railway_params)
    
    # Render deployment URL  
    render_params = {
        'repository': repo_url,
        'branch': branch
    }
    render_url = "https://render.com/deploy?" + urllib.parse.urlencode(render_params)
    
    # Heroku deployment URL
    heroku_url = f"https://heroku.com/deploy?template={repo_url}/tree/{branch}"
    
    # Display options
    print("🎯 DEPLOYMENT OPTIONS:")
    print()
    
    print("1️⃣ RAILWAY (Recommended - Fastest HTTPS)")
    print(f"   URL: {railway_url}")
    print("   ✅ Automatic HTTPS, ✅ Free tier, ✅ Instant deploy")
    print()
    
    print("2️⃣ RENDER (Alternative - Reliable)")  
    print(f"   URL: {render_url}")
    print("   ✅ Automatic HTTPS, ✅ Free tier, ✅ GitHub integration")
    print()
    
    print("3️⃣ HEROKU (Traditional - Requires card)")
    print(f"   URL: {heroku_url}")
    print("   ✅ Proven platform, ❌ Requires credit card verification")
    print()
    
    # Interactive deployment
    print("🖱️ INTERACTIVE DEPLOYMENT:")
    print()
    
    choice = input("Choose deployment platform (1=Railway, 2=Render, 3=Heroku, Enter=show all): ").strip()
    
    if choice == "1":
        print("🚂 Opening Railway deployment...")
        webbrowser.open(railway_url)
        return railway_url
    elif choice == "2":
        print("🎨 Opening Render deployment...")
        webbrowser.open(render_url)
        return render_url
    elif choice == "3":
        print("🟣 Opening Heroku deployment...")
        webbrowser.open(heroku_url)
        return heroku_url
    else:
        print("📋 Opening all deployment options...")
        webbrowser.open(railway_url)
        time.sleep(2)
        webbrowser.open(render_url)
        time.sleep(2)
        webbrowser.open(heroku_url)
        return "multiple"

def show_post_deployment_guide():
    """Display post-deployment validation instructions"""
    print()
    print("🔍 AFTER DEPLOYMENT - VALIDATION STEPS:")
    print("=" * 50)
    print()
    print("1️⃣ Note your deployment URL (e.g., https://your-app.railway.app)")
    print()
    print("2️⃣ Test your endpoints:")
    print("   # Health check")
    print("   curl -s YOUR_URL/health | jq .")
    print()
    print("   # System info")  
    print("   curl -s YOUR_URL/api/info | jq .")
    print()
    print("   # Fatigue analysis")
    print("   curl -s -X POST -H 'Content-Type: application/json' \\")
    print("     -d '{\"perclos\": 0.25, \"confidence\": 0.95}' \\")
    print("     YOUR_URL/api/analyze | jq .")
    print()
    print("3️⃣ Run comprehensive validation:")
    print("   python3 validate_deployment.py YOUR_URL")
    print()
    print("✅ EXPECTED RESULTS:")
    print("   • All endpoints return JSON responses")
    print("   • HTTPS automatically enabled")
    print("   • CORS headers present for ChatGPT compatibility")
    print("   • 100% fatigue detection accuracy maintained")
    print("   • Sub-100ms response times")

def main():
    """Main deployment orchestration"""
    try:
        deployment_url = create_deployment_urls()
        show_post_deployment_guide()
        
        if deployment_url and deployment_url != "multiple":
            print()
            print(f"🎉 Deployment initiated at: {deployment_url}")
            
    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()