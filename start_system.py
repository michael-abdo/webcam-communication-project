#!/usr/bin/env python3
"""
Unified System Startup Script - Foundation First

This script ensures proper system startup using the core pipeline
with enforced foundation validation.
"""

import sys
import os
import time
import subprocess

# Import core pipeline
from core_pipeline import pipeline, quick_start

def print_header():
    """Print system header."""
    print("\n" + "=" * 60)
    print("🏗️  WEBCAM COMMUNICATION SYSTEM - FOUNDATION FIRST")
    print("=" * 60)
    print("Built on solid foundations • Camera health validated first")
    print("Core Pipeline with Enforced Validation")
    print("=" * 60 + "\n")

def validate_foundation():
    """Validate foundation using core pipeline."""
    print("🎯 STEP 1: VALIDATING CAMERA FOUNDATION...")
    print("-" * 40)
    
    try:
        # Use core pipeline validation
        if pipeline.validator.validate_layer('foundation'):
            print("\n✅ FOUNDATION SOLID - Camera test passed!")
            print("   Camera is healthy and active")
            return True
        else:
            print("\n❌ FOUNDATION FAILED - Camera not working!")
            print("   Please fix camera issues before proceeding")
            return False
            
    except Exception as e:
        print(f"\n❌ Foundation test error: {e}")
        print("   Make sure camera is connected and accessible")
        return False

def show_system_menu():
    """Display system menu options."""
    print("\n📋 SYSTEM OPTIONS (Foundation Validated)")
    print("-" * 40)
    print("1. Camera Status Dashboard (http://localhost:5002)")
    print("2. Original Fatigue Demo (http://localhost:5000)")
    print("3. ⚡ ENFORCED Dashboard (Core Pipeline)")
    print("4. Run All Camera Tools")
    print("5. Pipeline Status Report")
    print("6. Exit")
    print("-" * 40)
    
    return input("Select option (1-6): ")

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

def start_enforced_dashboard():
    """Start enforced dashboard with core pipeline."""
    print("\n⚡ Starting ENFORCED Dashboard (Core Pipeline)...")
    print("This uses strict foundation enforcement!")
    print("Access at: http://localhost:5000")
    subprocess.Popen([sys.executable, "enforced_dashboard.py"])
    time.sleep(2)

def show_pipeline_status():
    """Show current pipeline status."""
    print("\n📊 PIPELINE STATUS REPORT")
    pipeline.status_report()

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
            start_enforced_dashboard()
        elif choice == '4':
            run_camera_tools()
        elif choice == '5':
            show_pipeline_status()
        elif choice == '6':
            print("\n👋 Exiting system. Foundation remains solid!")
            break
        else:
            print("\n❌ Invalid choice. Please select 1-6.")
        
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