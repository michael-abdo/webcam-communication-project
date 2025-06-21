#!/usr/bin/env python3
"""
Camera Diagnostics Tool
Comprehensive camera troubleshooting and analysis
"""

import cv2
import numpy as np
import time
import os
import platform

def diagnose_camera(index=0):
    """Run comprehensive diagnostics on a camera."""
    print(f"\n🔍 DIAGNOSING CAMERA {index}")
    print("=" * 50)
    
    # 1. Basic connectivity test
    print("\n1. CONNECTIVITY TEST")
    cap = cv2.VideoCapture(index)
    
    if not cap.isOpened():
        print("   ❌ Cannot connect to camera")
        return
    
    print("   ✅ Camera connected")
    
    # 2. Properties check
    print("\n2. CAMERA PROPERTIES")
    properties = {
        'Width': cv2.CAP_PROP_FRAME_WIDTH,
        'Height': cv2.CAP_PROP_FRAME_HEIGHT,
        'FPS': cv2.CAP_PROP_FPS,
        'Brightness': cv2.CAP_PROP_BRIGHTNESS,
        'Contrast': cv2.CAP_PROP_CONTRAST,
        'Saturation': cv2.CAP_PROP_SATURATION,
        'Exposure': cv2.CAP_PROP_EXPOSURE,
        'Auto Exposure': cv2.CAP_PROP_AUTO_EXPOSURE,
        'Gain': cv2.CAP_PROP_GAIN,
        'Focus': cv2.CAP_PROP_FOCUS,
        'Auto Focus': cv2.CAP_PROP_AUTOFOCUS,
        'White Balance': cv2.CAP_PROP_WB_TEMPERATURE,
        'Backend': cv2.CAP_PROP_BACKEND
    }
    
    for prop_name, prop_id in properties.items():
        value = cap.get(prop_id)
        if value != -1:
            print(f"   {prop_name}: {value}")
    
    # 3. Frame capture analysis
    print("\n3. FRAME CAPTURE ANALYSIS")
    print("   Capturing 30 frames for analysis...")
    
    frame_stats = []
    capture_times = []
    
    for i in range(30):
        start_time = time.time()
        ret, frame = cap.read()
        capture_time = time.time() - start_time
        capture_times.append(capture_time)
        
        if ret and frame is not None:
            # Analyze frame
            mean_val = np.mean(frame)
            std_val = np.std(frame)
            min_val = np.min(frame)
            max_val = np.max(frame)
            
            frame_stats.append({
                'mean': mean_val,
                'std': std_val,
                'min': min_val,
                'max': max_val
            })
            
            # Special checks
            if i == 0:
                print(f"\n   First frame analysis:")
                print(f"   - Shape: {frame.shape}")
                print(f"   - Data type: {frame.dtype}")
                print(f"   - Mean pixel value: {mean_val:.2f}")
                print(f"   - Std deviation: {std_val:.2f}")
                print(f"   - Min/Max values: {min_val}/{max_val}")
                
                # Check if frame is all black
                if max_val < 10:
                    print("   ⚠️  WARNING: Frame appears to be black!")
                    print("      Possible causes:")
                    print("      - Camera lens is covered")
                    print("      - Camera privacy shutter is closed")
                    print("      - Insufficient lighting")
                    print("      - Camera hardware issue")
                
                # Check if frame is uniform
                if std_val < 1:
                    print("   ⚠️  WARNING: Frame has very low variation!")
                    print("      This might indicate a virtual/synthetic camera")
    
    # Calculate statistics
    if frame_stats:
        avg_mean = np.mean([s['mean'] for s in frame_stats])
        avg_std = np.mean([s['std'] for s in frame_stats])
        avg_capture_time = np.mean(capture_times) * 1000  # Convert to ms
        
        print(f"\n   Overall statistics (30 frames):")
        print(f"   - Average brightness: {avg_mean:.2f}")
        print(f"   - Average variation: {avg_std:.2f}")
        print(f"   - Average capture time: {avg_capture_time:.2f}ms")
        print(f"   - Effective FPS: {1000/avg_capture_time:.1f}")
    
    # 4. Multi-format test
    print("\n4. FORMAT COMPATIBILITY TEST")
    formats = [
        ('MJPEG', cv2.VideoWriter_fourcc('M','J','P','G')),
        ('YUYV', cv2.VideoWriter_fourcc('Y','U','Y','V')),
        ('Default', -1)
    ]
    
    original_fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    
    for format_name, fourcc in formats:
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        ret, frame = cap.read()
        
        if ret:
            print(f"   ✅ {format_name} format: Supported")
        else:
            print(f"   ❌ {format_name} format: Not supported")
    
    # Restore original format
    cap.set(cv2.CAP_PROP_FOURCC, original_fourcc)
    
    # 5. Permission and access check
    print("\n5. SYSTEM PERMISSIONS")
    
    if platform.system() == "Darwin":  # macOS
        print("   📱 macOS detected")
        print("   To verify camera permissions:")
        print("   1. System Preferences → Security & Privacy → Privacy → Camera")
        print("   2. Ensure Terminal/Python has camera access")
        
    elif platform.system() == "Windows":
        print("   🪟 Windows detected")
        print("   To verify camera permissions:")
        print("   1. Settings → Privacy → Camera")
        print("   2. Allow apps to access camera")
        
    elif platform.system() == "Linux":
        print("   🐧 Linux detected")
        print("   Check camera permissions with:")
        print("   $ ls -la /dev/video*")
    
    # 6. Alternative access methods
    print("\n6. ALTERNATIVE ACCESS TEST")
    
    # Try different backends
    backends = [
        ('Default', cv2.CAP_ANY),
        ('V4L2', cv2.CAP_V4L2),
        ('DirectShow', cv2.CAP_DSHOW),
        ('AVFoundation', cv2.CAP_AVFOUNDATION),
        ('GStreamer', cv2.CAP_GSTREAMER)
    ]
    
    cap.release()
    
    for backend_name, backend_id in backends:
        test_cap = cv2.VideoCapture(index, backend_id)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret:
                print(f"   ✅ {backend_name}: Working")
            else:
                print(f"   ⚠️  {backend_name}: Opens but no frames")
            test_cap.release()
        else:
            print(f"   ❌ {backend_name}: Not available")
    
    # 7. Final diagnosis
    print("\n7. DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if avg_mean < 10:
        print("   🔴 ISSUE: Camera producing black/dark frames")
        print("   RECOMMENDATIONS:")
        print("   - Check if camera lens is covered")
        print("   - Verify privacy shutter is open")
        print("   - Improve lighting conditions")
        print("   - Try a different camera application to verify")
    
    elif avg_std < 5:
        print("   🟡 ISSUE: Low image variation detected")
        print("   RECOMMENDATIONS:")
        print("   - This might be a virtual camera")
        print("   - Check if correct camera is selected")
        print("   - Verify camera is showing real scene")
    
    else:
        print("   🟢 Camera appears to be working normally")
        print(f"   - Average brightness: {avg_mean:.1f}")
        print(f"   - Good image variation: {avg_std:.1f}")
        print(f"   - Stable capture rate: {1000/avg_capture_time:.1f} fps")

def list_all_cameras():
    """List all available cameras with detailed info."""
    print("\n📹 AVAILABLE CAMERAS")
    print("=" * 50)
    
    found_cameras = []
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            backend = cap.getBackendName()
            
            # Try to get a frame
            ret, frame = cap.read()
            frame_ok = "✅" if ret else "❌"
            
            found_cameras.append(i)
            
            print(f"\nCamera {i}:")
            print(f"  Backend: {backend}")
            print(f"  Resolution: {width}x{height}")
            print(f"  FPS: {fps}")
            print(f"  Frame capture: {frame_ok}")
            
            cap.release()
    
    if not found_cameras:
        print("❌ No cameras found!")
    else:
        print(f"\n✅ Total cameras found: {len(found_cameras)}")
    
    return found_cameras

def main():
    """Main diagnostic routine."""
    print("🔧 CAMERA DIAGNOSTICS TOOL")
    print("Comprehensive camera troubleshooting")
    print("=" * 50)
    
    # List all cameras
    cameras = list_all_cameras()
    
    if not cameras:
        print("\n❌ No cameras detected. Please check:")
        print("   - Camera is connected")
        print("   - Camera drivers are installed")
        print("   - No other apps are using the camera")
        return
    
    # Diagnose each camera
    for cam_idx in cameras:
        diagnose_camera(cam_idx)
    
    print("\n✨ Diagnostics complete!")

if __name__ == "__main__":
    main()