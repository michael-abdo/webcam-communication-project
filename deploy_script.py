#!/usr/bin/env python3
"""
Automated Deployment Script for Fatigue Detection System
Deploys to Railway and Render with comprehensive validation

Requirements:
- GitHub CLI (gh) installed and authenticated
- Railway CLI (optional, for advanced features)
- Git configured with user credentials
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

class DeploymentManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deploy_branch = "deploy"
        self.validation_script = "validate_deployment.py"
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command, check=True, capture_output=True):
        """Execute shell command with error handling"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=check, 
                capture_output=capture_output,
                text=True,
                timeout=300
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", "ERROR")
            self.log(f"Error output: {e.stderr}", "ERROR")
            raise
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {command}", "ERROR")
            raise
            
    def check_prerequisites(self):
        """Verify all required tools and configurations"""
        self.log("🔍 Checking prerequisites...")
        
        # Check Git configuration
        try:
            git_user = self.run_command("git config user.name").stdout.strip()
            git_email = self.run_command("git config user.email").stdout.strip()
            if not git_user or not git_email:
                raise Exception("Git user.name and user.email must be configured")
            self.log(f"✅ Git configured for: {git_user} <{git_email}>")
        except Exception as e:
            self.log(f"❌ Git configuration issue: {e}", "ERROR")
            return False
            
        # Check GitHub CLI
        try:
            gh_status = self.run_command("gh auth status", check=False)
            if gh_status.returncode != 0:
                self.log("❌ GitHub CLI not authenticated. Run: gh auth login", "ERROR")
                return False
            self.log("✅ GitHub CLI authenticated")
        except FileNotFoundError:
            self.log("❌ GitHub CLI not installed. Install from: https://cli.github.com/", "ERROR")
            return False
            
        # Check deployment files
        required_files = [
            "app.py", "requirements.txt", "Procfile", 
            "railway.json", "render.yaml", "runtime.txt"
        ]
        
        for file in required_files:
            if not (self.project_root / file).exists():
                self.log(f"❌ Missing required file: {file}", "ERROR")
                return False
                
        self.log("✅ All deployment files present")
        return True
        
    def setup_repository(self):
        """Fork repository and prepare for deployment"""
        self.log("🍴 Setting up repository...")
        
        # Get current repository info
        try:
            remote_url = self.run_command("git remote get-url origin").stdout.strip()
            if "github.com" not in remote_url:
                self.log(f"❌ Not a GitHub repository: {remote_url}", "ERROR")
                return False
                
            # Extract owner/repo from URL
            if remote_url.startswith("git@"):
                # SSH format: git@github.com:owner/repo.git
                repo_part = remote_url.split(":")[1].replace(".git", "")
            else:
                # HTTPS format: https://github.com/owner/repo.git
                repo_part = remote_url.split("github.com/")[1].replace(".git", "")
                
            original_owner, repo_name = repo_part.split("/")
            self.log(f"📦 Repository: {original_owner}/{repo_name}")
            
        except Exception as e:
            self.log(f"❌ Failed to get repository info: {e}", "ERROR")
            return False
            
        # Check if already forked
        try:
            current_user = self.run_command("gh api user --jq .login").stdout.strip()
            fork_check = self.run_command(f"gh repo view {current_user}/{repo_name}", check=False)
            
            if fork_check.returncode == 0:
                self.log(f"✅ Fork already exists: {current_user}/{repo_name}")
                self.fork_url = f"https://github.com/{current_user}/{repo_name}"
            else:
                # Create fork
                self.log("🔄 Creating repository fork...")
                self.run_command(f"gh repo fork {original_owner}/{repo_name} --clone=false")
                self.fork_url = f"https://github.com/{current_user}/{repo_name}"
                self.log(f"✅ Fork created: {self.fork_url}")
                
        except Exception as e:
            self.log(f"❌ Failed to fork repository: {e}", "ERROR")
            return False
            
        # Ensure deploy branch exists and is pushed
        try:
            # Check if deploy branch exists locally
            branch_check = self.run_command("git branch --list deploy", check=False)
            if not branch_check.stdout.strip():
                self.log("❌ Deploy branch not found locally", "ERROR")
                return False
                
            # Push deploy branch to fork
            self.log("📤 Pushing deploy branch to fork...")
            self.run_command(f"git push origin {self.deploy_branch}")
            self.log(f"✅ Deploy branch pushed to fork")
            
        except Exception as e:
            self.log(f"❌ Failed to push deploy branch: {e}", "ERROR")
            return False
            
        return True
        
    def deploy_to_railway(self):
        """Deploy to Railway using CLI if available, otherwise provide instructions"""
        self.log("🚂 Deploying to Railway...")
        
        # Check if Railway CLI is available
        try:
            railway_check = self.run_command("railway --version", check=False)
            if railway_check.returncode != 0:
                return self.railway_manual_instructions()
        except FileNotFoundError:
            return self.railway_manual_instructions()
            
        # Check Railway authentication
        try:
            self.run_command("railway whoami")
            self.log("✅ Railway CLI authenticated")
        except subprocess.CalledProcessError:
            self.log("❌ Railway CLI not authenticated. Run: railway login", "ERROR")
            return False
            
        try:
            # Create new Railway project
            self.log("🔄 Creating Railway project...")
            project_result = self.run_command("railway project new")
            
            # Connect GitHub repository
            self.log("🔗 Connecting GitHub repository...")
            self.run_command(f"railway connect github {self.fork_url}")
            
            # Deploy
            self.log("🚀 Deploying to Railway...")
            deploy_result = self.run_command("railway up")
            
            # Get deployment URL
            url_result = self.run_command("railway domain")
            railway_url = url_result.stdout.strip()
            
            if railway_url:
                self.log(f"✅ Railway deployment successful!")
                self.log(f"🌐 Railway URL: {railway_url}")
                return railway_url
            else:
                self.log("⚠️ Railway deployed but URL not available yet", "WARN")
                return "railway-pending"
                
        except Exception as e:
            self.log(f"❌ Railway deployment failed: {e}", "ERROR")
            return False
            
    def railway_manual_instructions(self):
        """Provide manual Railway deployment instructions"""
        self.log("📋 Railway CLI not available - providing manual instructions")
        
        instructions = f"""
🚂 MANUAL RAILWAY DEPLOYMENT:
1. Visit: https://railway.app
2. Click 'Deploy Now'
3. Login with GitHub
4. Select repository: {getattr(self, 'fork_url', 'your-fork')}
5. Choose branch: {self.deploy_branch}
6. Click 'Deploy'

Your app will be available at: https://your-app-name.railway.app
        """
        
        self.log(instructions)
        return "railway-manual"
        
    def deploy_to_render(self):
        """Deploy to Render using webhook approach"""
        self.log("🎨 Setting up Render deployment...")
        
        instructions = f"""
🎨 RENDER DEPLOYMENT:
1. Visit: https://render.com
2. Create account with GitHub
3. Click 'New Web Service'
4. Select repository: {getattr(self, 'fork_url', 'your-fork')}
5. Choose branch: {self.deploy_branch}
6. Render will auto-detect render.yaml configuration
7. Click 'Create Web Service'

Your app will be available at: https://your-app-name.onrender.com
        """
        
        self.log(instructions)
        return "render-manual"
        
    def validate_deployment(self, url):
        """Validate deployment using our validation script"""
        if url in ["railway-manual", "render-manual", "railway-pending"]:
            self.log("⏭️ Skipping validation - manual deployment required")
            return True
            
        self.log(f"🧪 Validating deployment: {url}")
        
        try:
            # Wait for deployment to be ready
            self.log("⏳ Waiting for deployment to be ready...")
            time.sleep(30)
            
            # Run validation script
            validation_cmd = f"python3 {self.validation_script} {url}"
            result = self.run_command(validation_cmd)
            
            if "🎉 DEPLOYMENT VALIDATED" in result.stdout:
                self.log("✅ Deployment validation successful!")
                return True
            else:
                self.log("❌ Deployment validation failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Validation error: {e}", "ERROR")
            return False
            
    def deploy(self):
        """Main deployment orchestration"""
        self.log("🚀 Starting automated deployment process...")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.log("❌ Prerequisites check failed", "ERROR")
            return False
            
        # Setup repository
        if not self.setup_repository():
            self.log("❌ Repository setup failed", "ERROR")
            return False
            
        # Deploy to platforms
        deployment_results = {}
        
        # Railway deployment
        railway_result = self.deploy_to_railway()
        deployment_results['railway'] = railway_result
        
        # Render deployment
        render_result = self.deploy_to_render()
        deployment_results['render'] = render_result
        
        # Validate deployments
        for platform, url in deployment_results.items():
            if url and url not in ["railway-manual", "render-manual", "railway-pending"]:
                self.validate_deployment(url)
                
        # Summary
        self.log("🎯 DEPLOYMENT SUMMARY")
        self.log("=" * 50)
        
        for platform, result in deployment_results.items():
            if result:
                if result in ["railway-manual", "render-manual"]:
                    self.log(f"📋 {platform.upper()}: Manual setup required (see instructions above)")
                elif result == "railway-pending":
                    self.log(f"⏳ {platform.upper()}: Deployed, URL pending")
                else:
                    self.log(f"✅ {platform.upper()}: {result}")
            else:
                self.log(f"❌ {platform.upper()}: Failed")
                
        self.log("🎉 Deployment process complete!")
        return True

def main():
    """Entry point for deployment script"""
    print("🚀 FATIGUE DETECTION SYSTEM - AUTOMATED DEPLOYMENT")
    print("=" * 60)
    
    deployer = DeploymentManager()
    
    try:
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        deployer.log("❌ Deployment cancelled by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        deployer.log(f"❌ Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()