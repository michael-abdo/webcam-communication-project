#!/usr/bin/env python3
"""
Camera Permissions Checker
Verify camera access permissions on different platforms
"""

import platform
import subprocess
import os
import sys

def check_macos_permissions():
    """Check camera permissions on macOS."""
    print("\n🍎 macOS Camera Permissions Check")
    print("=" * 50)
    
    # Check if we're running in Terminal
    print("\n1. Current Process Info:")
    print(f"   Python executable: {sys.executable}")
    print(f"   Process ID: {os.getpid()}")
    
    # Check camera privacy settings using tccutil
    print("\n2. Camera Access Status:")
    
    # Try to check TCC database (requires admin for full access)
    try:
        # Check if Terminal has camera access
        result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to get properties'],
            capture_output=True,
            text=True
        )
        print("   ✅ System Events accessible")
    except:
        print("   ⚠️  Cannot query System Events")
    
    # Instructions for manual check
    print("\n3. Manual Verification Steps:")
    print("   a) Open System Preferences → Security & Privacy → Privacy → Camera")
    print("   b) Look for these applications:")
    print("      - Terminal")
    print("      - Python")
    print("      - Your IDE (if using one)")
    print("   c) Ensure they have checkmarks for camera access")
    
    # Test camera access directly
    print("\n4. Direct Camera Test:")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("   ✅ Camera can be accessed by OpenCV")
            ret, frame = cap.read()
            if ret:
                print("   ✅ Can capture frames")
            else:
                print("   ❌ Cannot capture frames (permission issue?)")
            cap.release()
        else:
            print("   ❌ Cannot open camera (permission denied?)")
    except ImportError:
        print("   ⚠️  OpenCV not installed")
    
    # Check for camera devices
    print("\n5. Camera Devices:")
    try:
        result = subprocess.run(
            ['system_profiler', 'SPCameraDataType'],
            capture_output=True,
            text=True
        )
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Model ID:' in line or 'Unique ID:' in line:
                    print(f"   {line.strip()}")
        else:
            print("   No camera information available")
    except:
        print("   Cannot query camera devices")

def check_windows_permissions():
    """Check camera permissions on Windows."""
    print("\n🪟 Windows Camera Permissions Check")
    print("=" * 50)
    
    print("\n1. Manual Verification Steps:")
    print("   a) Open Settings → Privacy → Camera")
    print("   b) Ensure 'Allow apps to access your camera' is ON")
    print("   c) Scroll down and ensure Python/your app has access")
    
    print("\n2. PowerShell Check:")
    print("   Run this in PowerShell as Administrator:")
    print("   Get-PnpDevice -Class Camera -Status OK")

def check_linux_permissions():
    """Check camera permissions on Linux."""
    print("\n🐧 Linux Camera Permissions Check")
    print("=" * 50)
    
    print("\n1. Video Device Permissions:")
    try:
        result = subprocess.run(['ls', '-la', '/dev/video*'], 
                              capture_output=True, text=True, shell=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("   No video devices found")
    except:
        print("   Cannot list video devices")
    
    print("\n2. Current User Groups:")
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        print(f"   Groups: {result.stdout.strip()}")
        if 'video' not in result.stdout:
            print("   ⚠️  User not in 'video' group")
            print("   Fix: sudo usermod -a -G video $USER")
    except:
        pass
    
    print("\n3. V4L2 Check:")
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
    except:
        print("   v4l2-utils not installed (install with: sudo apt install v4l2-utils)")

def check_camera_access():
    """Comprehensive camera access check."""
    print("🔒 CAMERA PERMISSIONS CHECKER")
    print("Verify camera access and permissions")
    
    # Detect platform
    system = platform.system()
    
    if system == "Darwin":
        check_macos_permissions()
    elif system == "Windows":
        check_windows_permissions()
    elif system == "Linux":
        check_linux_permissions()
    else:
        print(f"Unknown platform: {system}")
    
    # Universal camera test
    print("\n📸 Universal Camera Test")
    print("=" * 50)
    
    try:
        import cv2
        
        # Test multiple camera indices
        cameras_found = []
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    cameras_found.append(i)
                cap.release()
        
        if cameras_found:
            print(f"✅ Accessible cameras: {cameras_found}")
            print("✅ Camera permissions appear to be GRANTED")
        else:
            print("❌ No accessible cameras found")
            print("❌ Camera permissions may be DENIED")
            
    except ImportError:
        print("⚠️  OpenCV not available for testing")
    
    # Final recommendations
    print("\n💡 Recommendations:")
    print("=" * 50)
    
    if system == "Darwin":
        print("1. If camera access is denied:")
        print("   - Quit Terminal/Python completely")
        print("   - Go to System Preferences → Security & Privacy → Privacy → Camera")
        print("   - Add Terminal or your Python IDE")
        print("   - Restart your application")
        print("\n2. For VS Code users:")
        print("   - You may need to run VS Code from Terminal: 'code .'")
        print("   - Or grant camera access to 'Code' in Privacy settings")
    
    print("\n✨ Permissions check complete!")

if __name__ == "__main__":
    check_camera_access()