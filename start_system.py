#!/usr/bin/env python3
"""
Unified System Startup Script - Foundation First

This script ensures proper system startup by validating camera health
before launching any advanced features.
"""

import sys
import os
import time
import subprocess

# Add camera tools to path
sys.path.append('./camera_tools/tests')

def print_header():
    """Print system header."""
    print("\n" + "=" * 60)
    print("🏗️  WEBCAM COMMUNICATION SYSTEM - FOUNDATION FIRST")
    print("=" * 60)
    print("Built on solid foundations • Camera health validated first")
    print("=" * 60 + "\n")

def validate_foundation():
    """Run foundation camera test."""
    print("🎯 STEP 1: VALIDATING CAMERA FOUNDATION...")
    print("-" * 40)
    
    try:
        # Import and run camera test
        from quick_camera_test import test_camera
        
        # Test primary camera
        camera_healthy = test_camera(0)
        
        if camera_healthy:
            print("\n✅ FOUNDATION SOLID - Camera test passed!")
            print("   Camera is healthy and active")
            return True
        else:
            print("\n❌ FOUNDATION FAILED - Camera not working!")
            print("   Please fix camera issues before proceeding")
            return False
            
    except Exception as e:
        print(f"\n❌ Foundation test error: {e}")
        print("   Make sure you're running from project root directory")
        return False

def show_system_menu():
    """Display system menu options."""
    print("\n📋 SYSTEM OPTIONS (Foundation Validated)")
    print("-" * 40)
    print("1. Camera Status Dashboard (http://localhost:5002)")
    print("2. Fatigue Detection Demo (http://localhost:5000)")
    print("3. Integrated System (Full Features)")
    print("4. Run All Camera Tools")
    print("5. Exit")
    print("-" * 40)
    
    return input("Select option (1-5): ")

def start_camera_dashboard():
    """Start camera status dashboard."""
    print("\n📹 Starting Camera Status Dashboard...")
    print("Access at: http://localhost:5002")
    subprocess.Popen([sys.executable, "camera_tools/dashboards/camera_status_dashboard.py"])
    time.sleep(2)

def start_fatigue_demo():
    """Start fatigue detection demo."""
    print("\n🧠 Starting Fatigue Detection Demo...")
    print("Access at: http://localhost:5000")
    print("⚠️  Remember to validate foundation in the web interface!")
    subprocess.Popen([sys.executable, "demo_dashboard.py"])
    time.sleep(2)

def start_integrated_system():
    """Start integrated system with all features."""
    print("\n🚀 Starting Integrated System...")
    print("Access at: http://localhost:5000")
    subprocess.Popen([sys.executable, "integrated_fatigue_system.py"])
    time.sleep(2)

def run_camera_tools():
    """Run camera tools menu."""
    print("\n🔧 Running Camera Tools...")
    subprocess.run([sys.executable, "camera_tools/run_camera_tool.py"])

def main():
    """Main startup flow."""
    print_header()
    
    # FOUNDATION RULE: Always validate camera first
    foundation_valid = validate_foundation()
    
    if not foundation_valid:
        print("\n🛑 CANNOT PROCEED WITHOUT SOLID FOUNDATION")
        print("Please resolve camera issues and try again.")
        print("\nTroubleshooting steps:")
        print("1. Check if camera is connected")
        print("2. Close other apps using camera")
        print("3. Check system permissions")
        print("4. Run: python3 camera_tools/diagnostics/camera_diagnostics.py")
        sys.exit(1)
    
    # Foundation is solid, show options
    while True:
        choice = show_system_menu()
        
        if choice == '1':
            start_camera_dashboard()
        elif choice == '2':
            start_fatigue_demo()
        elif choice == '3':
            start_integrated_system()
        elif choice == '4':
            run_camera_tools()
        elif choice == '5':
            print("\n👋 Exiting system. Foundation remains solid!")
            break
        else:
            print("\n❌ Invalid choice. Please select 1-5.")
        
        # Give time for subprocess to start
        if choice in ['1', '2', '3']:
            print("\n✅ Service started in background")
            input("Press Enter to continue...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 System shutdown requested")
        print("Foundation validation complete - camera remains healthy")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        print("Please check error and ensure foundation is solid")