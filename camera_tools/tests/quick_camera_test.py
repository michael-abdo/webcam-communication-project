#!/usr/bin/env python3
"""
Quick Camera Test - Verify camera is active and working
"""

import cv2
import numpy as np
import time

def test_camera(index=0):
    """Test a specific camera index."""
    print(f"\n🎥 Testing Camera {index}")
    print("-" * 40)
    
    # Try to open camera
    cap = cv2.VideoCapture(index)
    
    if not cap.isOpened():
        print(f"❌ Camera {index} cannot be opened")
        return False
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Get camera info
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.getBackendName()
    
    print(f"✅ Camera {index} opened successfully")
    print(f"   Backend: {backend}")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    
    # Try to capture frames
    print(f"\n📸 Capturing test frames...")
    frames_captured = 0
    frames_failed = 0
    
    for i in range(10):
        ret, frame = cap.read()
        
        if ret and frame is not None:
            frames_captured += 1
            
            # Analyze frame
            mean_brightness = np.mean(frame)
            is_color = len(frame.shape) == 3
            actual_height, actual_width = frame.shape[:2]
            
            if i == 0:  # Print details for first frame
                print(f"\n   Frame details:")
                print(f"   - Dimensions: {actual_width}x{actual_height}")
                print(f"   - Color: {'Yes' if is_color else 'No'}")
                print(f"   - Mean brightness: {mean_brightness:.1f}")
                print(f"   - Frame not empty: {'Yes' if mean_brightness > 5 else 'No (possibly covered)'}")
                
        else:
            frames_failed += 1
        
        time.sleep(0.1)  # Small delay between captures
    
    print(f"\n   Capture results:")
    print(f"   - Frames captured: {frames_captured}/10")
    print(f"   - Success rate: {frames_captured * 10}%")
    
    # Save a test frame
    if frames_captured > 0:
        ret, frame = cap.read()
        if ret:
            filename = f"camera_{index}_test_frame.jpg"
            cv2.imwrite(filename, frame)
            print(f"   - Test frame saved: {filename}")
    
    cap.release()
    
    # Overall verdict
    if frames_captured >= 8:
        print(f"\n✅ Camera {index} is HEALTHY and ACTIVE")
        return True
    elif frames_captured >= 5:
        print(f"\n⚠️  Camera {index} is PARTIALLY WORKING")
        return True
    else:
        print(f"\n❌ Camera {index} is NOT WORKING PROPERLY")
        return False

def main():
    """Main function to test all cameras."""
    print("🎥 CAMERA VERIFICATION TOOL")
    print("=" * 40)
    
    # Test available cameras
    working_cameras = []
    
    for i in range(2):  # Test first 2 camera indices
        if test_camera(i):
            working_cameras.append(i)
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 SUMMARY")
    print("-" * 40)
    
    if working_cameras:
        print(f"✅ Found {len(working_cameras)} working camera(s): {working_cameras}")
        print("\n🎬 Camera Status: ACTIVE")
        
        # Show which camera to use
        recommended = working_cameras[0]
        print(f"\n💡 Recommended camera: Index {recommended}")
        print(f"   Use this in your applications with:")
        print(f"   cap = cv2.VideoCapture({recommended})")
    else:
        print("❌ No working cameras found!")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check if camera is being used by another app")
        print("   2. Check system privacy settings for camera access")
        print("   3. Try restarting your computer")
        print("   4. Update camera drivers")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    main()