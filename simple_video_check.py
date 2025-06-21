#!/usr/bin/env python3
"""
Simple video validation without MediaPipe
Just checks if videos can be opened and displays basic info
"""

import cv2
import os
import json
from datetime import datetime

def check_video(video_path):
    """Check if video can be opened and get basic info."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    # Read first frame to verify
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    return {
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration": duration,
        "resolution": f"{width}x{height}"
    }

def validate_videos():
    """Validate all videos in the cognitive_overload directory."""
    base_dir = "cognitive_overload/validation"
    results = {
        "timestamp": datetime.now().isoformat(),
        "videos_found": 0,
        "videos_valid": 0,
        "video_details": []
    }
    
    # Find all video files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov')):
                video_path = os.path.join(root, file)
                relative_path = os.path.relpath(video_path, base_dir)
                
                print(f"Checking: {relative_path}")
                results["videos_found"] += 1
                
                info = check_video(video_path)
                if info:
                    results["videos_valid"] += 1
                    results["video_details"].append({
                        "file": relative_path,
                        "valid": True,
                        **info
                    })
                    print(f"  ✓ Valid - {info['resolution']} @ {info['fps']:.1f}fps, {info['duration']:.1f}s")
                else:
                    results["video_details"].append({
                        "file": relative_path,
                        "valid": False
                    })
                    print(f"  ✗ Invalid video")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Videos found: {results['videos_found']}")
    print(f"Videos valid: {results['videos_valid']}")
    print(f"Success rate: {results['videos_valid']/results['videos_found']*100:.1f}%")
    
    # Save results
    output_file = "video_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    print("Simple Video Validation (No MediaPipe Required)")
    print("=" * 50)
    validate_videos()