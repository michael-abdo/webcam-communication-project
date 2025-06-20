#!/usr/bin/env python3
"""
Quick Validation on Existing Test Videos

This script quickly validates the system using existing test videos
without requiring external datasets.
"""

import os
import sys
sys.path.append('..')

from dataset_validator import DatasetValidator

def main():
    """Run quick validation on existing test videos."""
    print("=== QUICK VALIDATION ON EXISTING VIDEOS ===")
    
    # Use existing test videos directory
    test_videos_dir = "../tests/test_videos"
    
    if not os.path.exists(test_videos_dir):
        print(f"❌ Test videos directory not found: {test_videos_dir}")
        return
    
    # Create validator
    validator = DatasetValidator(test_videos_dir, "./quick_validation_results")
    
    # Run validation
    print(f"Validating videos in: {test_videos_dir}")
    results = validator.validate_dataset(max_videos=5)
    
    # Analyze specific results
    print("\n=== DETAILED RESULTS ===")
    
    real_face_videos = []
    synthetic_videos = []
    
    for video_result in results['video_results']:
        if video_result['processing_successful']:
            filename = video_result['file_name']
            detection_rate = video_result['processing_metrics']['detection_rate']
            
            if 'synthetic' in filename or 'test_face' in filename:
                synthetic_videos.append((filename, detection_rate))
            else:
                real_face_videos.append((filename, detection_rate))
    
    print("\nSynthetic Videos:")
    for name, rate in synthetic_videos:
        print(f"  {name}: {rate:.1%} detection")
    
    print("\nOther Test Videos:")
    for name, rate in real_face_videos:
        print(f"  {name}: {rate:.1%} detection")
    
    # Recommendation
    print("\n=== RECOMMENDATION ===")
    avg_detection = results['aggregate_metrics']['average_detection_rate']
    
    if avg_detection > 0.7:
        print("✅ System shows good detection rates on test videos")
        print("   Next step: Validate with real human webcam videos")
    else:
        print("⚠️  Low detection rates on test videos")
        print("   The simple test patterns are not sufficient for MediaPipe")
        print("   Real human face videos are required for proper validation")

if __name__ == "__main__":
    main()