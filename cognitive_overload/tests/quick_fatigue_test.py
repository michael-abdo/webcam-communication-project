#!/usr/bin/env python3
"""
Quick fatigue detection test using existing infrastructure.
Tests PERCLOS on the synthetic tired face video.
"""

import sys
sys.path.append('../processing')

from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
import numpy as np

def quick_perclos_test():
    """
    Quick PERCLOS calculation using existing eye tracking.
    Tests on synthetic_tired.mp4 which should show fatigue.
    """
    
    # Test videos - tired should show higher PERCLOS than neutral
    test_videos = {
        'tired': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_tired.mp4',
        'neutral': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4',
        'focused': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_focused.mp4'
    }
    
    # PERCLOS threshold - eyes closed when openness < 0.2 (80% closed)
    EYE_CLOSED_THRESHOLD = 0.2
    
    print("=== QUICK FATIGUE DETECTION TEST ===")
    print("Testing PERCLOS (Percentage of Eyelid Closure)")
    print(f"Threshold: Eye openness < {EYE_CLOSED_THRESHOLD} = closed\n")
    
    results = {}
    
    for video_type, video_path in test_videos.items():
        print(f"\nTesting {video_type} video: {video_path}")
        
        try:
            # Use existing infrastructure
            processor = LandmarkProcessor(video_path)
            mapper = CognitiveLandmarkMapper()
            
            # Process video
            video_results = processor.process_video()
            
            # Calculate PERCLOS
            eye_openness_values = []
            
            for frame_data in video_results['landmarks_data']:
                if frame_data['face_detected']:
                    # Get eye metrics using existing system
                    metrics = mapper.get_cognitive_metrics(frame_data['landmarks'])
                    eye_openness_values.append(metrics['avg_eye_openness'])
            
            if eye_openness_values:
                # Calculate PERCLOS
                eyes_closed_count = sum(1 for openness in eye_openness_values 
                                      if openness < EYE_CLOSED_THRESHOLD)
                perclos = eyes_closed_count / len(eye_openness_values)
                
                # Calculate other statistics
                avg_openness = np.mean(eye_openness_values)
                min_openness = np.min(eye_openness_values)
                max_openness = np.max(eye_openness_values)
                
                # Determine fatigue level based on PERCLOS
                if perclos > 0.15:
                    fatigue_level = "DROWSY (High fatigue)"
                elif perclos > 0.08:
                    fatigue_level = "MODERATE fatigue"
                else:
                    fatigue_level = "ALERT"
                
                results[video_type] = {
                    'perclos': perclos,
                    'fatigue_level': fatigue_level,
                    'avg_openness': avg_openness,
                    'frames_analyzed': len(eye_openness_values)
                }
                
                print(f"  PERCLOS: {perclos:.1%}")
                print(f"  Fatigue Level: {fatigue_level}")
                print(f"  Avg Eye Openness: {avg_openness:.3f}")
                print(f"  Eye Openness Range: {min_openness:.3f} - {max_openness:.3f}")
                print(f"  Frames with face: {len(eye_openness_values)}")
                
        except Exception as e:
            print(f"  Error processing {video_type}: {e}")
    
    # Summary comparison
    print("\n=== SUMMARY COMPARISON ===")
    print("Expected: 'tired' video should show higher PERCLOS than 'neutral' and 'focused'")
    print("\nResults:")
    for video_type, data in results.items():
        print(f"  {video_type:8s}: PERCLOS={data['perclos']:.1%}, {data['fatigue_level']}")
    
    # Validation check
    if 'tired' in results and 'neutral' in results:
        if results['tired']['perclos'] > results['neutral']['perclos']:
            print("\n✅ VALIDATION PASSED: Tired video shows higher PERCLOS!")
            print("   The system can detect fatigue using existing eye tracking.")
        else:
            print("\n⚠️  Unexpected: Tired video doesn't show higher PERCLOS.")
            print("   May need threshold adjustment or video quality check.")
    
    print("\n=== NEXT STEPS ===")
    print("1. The eye tracking is already suitable for PERCLOS calculation!")
    print("2. Add temporal analysis (track PERCLOS over sliding windows)")
    print("3. Add blink detection (transitions from open->closed->open)")
    print("4. Test on real drowsy driver datasets for validation")
    
    return results

if __name__ == "__main__":
    quick_perclos_test()