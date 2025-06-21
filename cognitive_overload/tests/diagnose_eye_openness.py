#!/usr/bin/env python3
"""
Diagnose eye openness values to calibrate thresholds properly.
"""

import sys
sys.path.append('./cognitive_overload/processing')

from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
import numpy as np
import matplotlib.pyplot as plt


def diagnose_eye_openness():
    """Analyze actual eye openness values from different videos."""
    
    print("EYE OPENNESS DIAGNOSTIC")
    print("="*60)
    
    test_videos = {
        'Real Face': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4',
        'Synthetic Neutral': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4',
        'Synthetic Tired': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_tired.mp4'
    }
    
    all_results = {}
    
    for video_name, video_path in test_videos.items():
        print(f"\nAnalyzing: {video_name}")
        
        processor = LandmarkProcessor(video_path)
        mapper = CognitiveLandmarkMapper()
        
        video_results = processor.process_video()
        eye_openness_values = []
        
        # Sample first 100 frames
        for i, frame_data in enumerate(video_results['landmarks_data'][:100]):
            if frame_data.get('face_detected', False):
                landmarks = frame_data['landmarks']
                
                # Calculate eye openness
                left_openness = calculate_eye_openness_detailed(landmarks, mapper.left_eye_landmarks)
                right_openness = calculate_eye_openness_detailed(landmarks, mapper.right_eye_landmarks)
                
                avg_openness = (left_openness['ratio'] + right_openness['ratio']) / 2
                eye_openness_values.append({
                    'frame': i,
                    'avg_openness': avg_openness,
                    'left_openness': left_openness['ratio'],
                    'right_openness': right_openness['ratio'],
                    'left_vertical': left_openness['vertical'],
                    'left_horizontal': left_openness['horizontal'],
                    'right_vertical': right_openness['vertical'],
                    'right_horizontal': right_openness['horizontal']
                })
        
        if eye_openness_values:
            openness_list = [v['avg_openness'] for v in eye_openness_values]
            
            print(f"  Samples: {len(eye_openness_values)}")
            print(f"  Min openness: {min(openness_list):.4f}")
            print(f"  Max openness: {max(openness_list):.4f}")
            print(f"  Mean openness: {np.mean(openness_list):.4f}")
            print(f"  Std dev: {np.std(openness_list):.4f}")
            
            # Percentiles
            percentiles = [10, 25, 50, 75, 90]
            for p in percentiles:
                value = np.percentile(openness_list, p)
                print(f"  {p}th percentile: {value:.4f}")
            
            all_results[video_name] = {
                'values': eye_openness_values,
                'stats': {
                    'min': min(openness_list),
                    'max': max(openness_list),
                    'mean': np.mean(openness_list),
                    'std': np.std(openness_list),
                    'percentiles': {p: np.percentile(openness_list, p) for p in percentiles}
                }
            }
    
    # Recommend thresholds
    print("\n" + "="*60)
    print("THRESHOLD RECOMMENDATIONS")
    print("="*60)
    
    # Analyze distributions
    real_mean = all_results.get('Real Face', {}).get('stats', {}).get('mean', 0.15)
    synthetic_mean = all_results.get('Synthetic Neutral', {}).get('stats', {}).get('mean', 0.18)
    
    print(f"\nFor REAL faces:")
    print(f"  Eye closed threshold: {real_mean * 0.8:.3f} (80% of mean)")
    print(f"  PERCLOS threshold: 0.15 (standard)")
    
    print(f"\nFor SYNTHETIC faces:")
    print(f"  Eye closed threshold: {synthetic_mean * 0.8:.3f} (80% of mean)")
    print(f"  PERCLOS threshold: 0.15 (standard)")
    
    # Save diagnostic data
    import json
    with open('eye_openness_diagnostic.json', 'w') as f:
        json.dump({
            'analysis': {name: stats['stats'] for name, stats in all_results.items()},
            'recommendations': {
                'real_faces': {
                    'eye_closed_threshold': real_mean * 0.8,
                    'perclos_threshold': 0.15
                },
                'synthetic_faces': {
                    'eye_closed_threshold': synthetic_mean * 0.8,
                    'perclos_threshold': 0.15
                }
            }
        }, f, indent=2)
    
    print("\n💾 Diagnostic data saved to: eye_openness_diagnostic.json")
    
    return all_results


def calculate_eye_openness_detailed(landmarks, eye_landmarks_config):
    """Calculate eye openness with detailed measurements."""
    try:
        upper_lid = eye_landmarks_config['upper_lid'][:4]
        lower_lid = eye_landmarks_config['lower_lid'][:4]
        
        # Calculate vertical distances
        vertical_distances = []
        for i in range(min(len(upper_lid), len(lower_lid))):
            upper_point = landmarks[upper_lid[i]]
            lower_point = landmarks[lower_lid[i]]
            vertical_dist = abs(upper_point[1] - lower_point[1])
            vertical_distances.append(vertical_dist)
        
        avg_vertical = np.mean(vertical_distances)
        
        # Calculate horizontal distance
        inner_corner = landmarks[eye_landmarks_config['inner_corner'][0]]
        outer_corner = landmarks[eye_landmarks_config['outer_corner'][0]]
        horizontal_dist = abs(outer_corner[0] - inner_corner[0])
        
        # Eye openness ratio
        openness_ratio = avg_vertical / max(horizontal_dist, 0.001)
        
        return {
            'ratio': openness_ratio,
            'vertical': avg_vertical,
            'horizontal': horizontal_dist
        }
        
    except (IndexError, KeyError):
        return {
            'ratio': 0.15,
            'vertical': 0.01,
            'horizontal': 0.1
        }


if __name__ == "__main__":
    diagnose_eye_openness()