#!/usr/bin/env python3
"""
Camera Tools Runner
Main entry point for all camera tools
"""

import os
import sys
import subprocess

def display_menu():
    """Display the main menu."""
    print("\n🎥 CAMERA TOOLS SUITE")
    print("=" * 50)
    print("\n1. Quick Camera Test")
    print("2. Camera Diagnostics")
    print("3. Check Camera Permissions")
    print("4. Camera Quality Assessment")
    print("5. Health Monitor (Continuous)")
    print("6. Status Dashboard (Web)")
    print("7. View Output Files")
    print("0. Exit")
    print("\n" + "=" * 50)

def run_tool(script_path):
    """Run a camera tool script."""
    if os.path.exists(script_path):
        print(f"\n🚀 Running {os.path.basename(script_path)}...")
        print("-" * 50)
        subprocess.run([sys.executable, script_path])
    else:
        print(f"❌ Script not found: {script_path}")

def list_output_files():
    """List files in the output directory."""
    output_dir = "output"
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        if files:
            print("\n📁 Output Files:")
            print("-" * 50)
            for file in sorted(files):
                size = os.path.getsize(os.path.join(output_dir, file))
                print(f"  - {file} ({size:,} bytes)")
        else:
            print("\n📁 No output files found")
    else:
        print("\n📁 Output directory not found")

def main():
    """Main menu loop."""
    tools = {
        "1": "tests/quick_camera_test.py",
        "2": "diagnostics/camera_diagnostics.py",
        "3": "diagnostics/check_camera_permissions.py",
        "4": "tests/camera_quality_test.py",
        "5": "health_monitoring/webcam_health_monitor.py",
        "6": "dashboards/camera_status_dashboard.py"
    }
    
    while True:
        display_menu()
        choice = input("\n👉 Select an option (0-7): ").strip()
        
        if choice == "0":
            print("\n👋 Exiting Camera Tools Suite")
            break
        elif choice == "7":
            list_output_files()
            input("\nPress Enter to continue...")
        elif choice in tools:
            run_tool(tools[choice])
            input("\n✅ Press Enter to return to menu...")
        else:
            print("\n❌ Invalid option. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Change to camera_tools directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🎥 Welcome to Camera Tools Suite!")
    print("This suite provides comprehensive camera testing and monitoring tools.")
    
    # Check dependencies
    try:
        import cv2
        import numpy
    except ImportError:
        print("\n⚠️  Missing dependencies detected!")
        print("Please install required packages:")
        print("  pip install opencv-python numpy flask")
        sys.exit(1)
    
    main()