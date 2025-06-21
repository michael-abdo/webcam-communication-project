#!/usr/bin/env python3
"""
Fixed Eye Calculation Test - Uses correct CognitiveLandmarkMapper methods
This script properly integrates with the existing landmark infrastructure.
"""

import sys
sys.path.append('./cognitive_overload/processing')

from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
import numpy as np
import json
from datetime import datetime


def test_fixed_eye_calculation():
    """Test eye calculation using the correct CognitiveLandmarkMapper methods."""
    
    print("=" * 80)
    print("FIXED EYE CALCULATION TEST")
    print("Using CognitiveLandmarkMapper.calculate_eye_openness() with correct data format")
    print("=" * 80)
    
    # Test videos
    test_videos = [
        {
            'name': 'Real Human Face',
            'path': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4',
            'expected': 'Variable eye openness'
        },
        {
            'name': 'Synthetic Neutral',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4',
            'expected': 'Consistent eye openness'
        },
        {
            'name': 'Synthetic Tired',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_tired.mp4',
            'expected': 'Lower eye openness (tired)'
        }
    ]
    
    results = []
    
    for test_video in test_videos:
        print(f"\n{'='*60}")
        print(f"Testing: {test_video['name']}")
        print(f"Path: {test_video['path']}")
        print(f"Expected: {test_video['expected']}")
        print(f"{'='*60}")
        
        try:
            # Initialize components correctly
            processor = LandmarkProcessor(test_video['path'])
            mapper = CognitiveLandmarkMapper()
            fatigue_detector = FatigueDetector()
            
            # Process video using existing infrastructure
            video_results = processor.process_video()
            landmarks_data = video_results['landmarks_data']
            
            print(f"Processed {len(landmarks_data)} frames")
            
            # Test first 10 frames for detailed analysis
            eye_openness_values = []
            
            for i, frame_data in enumerate(landmarks_data[:10]):
                if frame_data.get('face_detected', False):
                    landmarks = frame_data['landmarks']
                    
                    # Use the CORRECT CognitiveLandmarkMapper methods
                    left_eye_openness = mapper.calculate_eye_openness(landmarks, 'left')
                    right_eye_openness = mapper.calculate_eye_openness(landmarks, 'right')
                    avg_openness = (left_eye_openness + right_eye_openness) / 2
                    
                    eye_openness_values.append({
                        'frame': i,
                        'left_eye': left_eye_openness,
                        'right_eye': right_eye_openness,
                        'average': avg_openness
                    })
                    
                    print(f"  Frame {i:2d}: L={left_eye_openness:.4f}, R={right_eye_openness:.4f}, Avg={avg_openness:.4f}")
            
            # Calculate statistics
            if eye_openness_values:
                avg_values = [v['average'] for v in eye_openness_values]
                
                stats = {
                    'min': min(avg_values),
                    'max': max(avg_values),
                    'mean': np.mean(avg_values),
                    'std': np.std(avg_values),
                    'range': max(avg_values) - min(avg_values)
                }
                
                print(f"\n📊 STATISTICS:")
                print(f"  Min openness: {stats['min']:.4f}")
                print(f"  Max openness: {stats['max']:.4f}")
                print(f"  Mean openness: {stats['mean']:.4f}")
                print(f"  Std deviation: {stats['std']:.4f}")
                print(f"  Range: {stats['range']:.4f}")
                
                # Test fatigue detector with corrected calculation
                print(f"\n🔬 FATIGUE DETECTION TEST:")
                fatigue_detector.set_calibration('real' if 'Real' in test_video['name'] else 'synthetic')
                
                for i, value in enumerate(avg_values[:5]):  # Test first 5 frames
                    metrics = fatigue_detector.update(value, i / 30.0)  # Simulate 30fps
                    print(f"  Frame {i}: Openness={value:.4f}, PERCLOS={metrics['perclos_percentage']:.1f}%, Level={metrics['fatigue_level']}")
                
                results.append({
                    'video': test_video['name'],
                    'path': test_video['path'],
                    'frames_analyzed': len(eye_openness_values),
                    'statistics': stats,
                    'sample_values': eye_openness_values,
                    'status': 'success'
                })
                
            else:
                print("❌ No eye openness values calculated")
                results.append({
                    'video': test_video['name'],
                    'path': test_video['path'],
                    'status': 'no_data',
                    'error': 'No eye openness values calculated'
                })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'video': test_video['name'],
                'path': test_video['path'],
                'status': 'error',
                'error': str(e)
            })
    
    # Save results
    save_test_results(results)
    
    # Print summary
    print_test_summary(results)
    
    return results


def save_test_results(results):
    """Save test results to file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'eye_calculation_fix_results_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'test_type': 'eye_calculation_fix',
            'results': results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")


def print_test_summary(results):
    """Print test summary."""
    print("\n" + "="*80)
    print("EYE CALCULATION FIX - TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    print(f"\n✅ Successful tests: {len(successful)}")
    print(f"❌ Failed tests: {len(failed)}")
    
    if successful:
        print(f"\n📊 EYE OPENNESS RANGES:")
        for result in successful:
            stats = result['statistics']
            print(f"  {result['video']}:")
            print(f"    Range: {stats['min']:.4f} - {stats['max']:.4f}")
            print(f"    Mean: {stats['mean']:.4f} ± {stats['std']:.4f}")
    
    if failed:
        print(f"\n❌ FAILED TESTS:")
        for result in failed:
            print(f"  {result['video']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n🎯 KEY FINDINGS:")
    if successful:
        # Check if we're getting variable values (not constant 0.15)
        all_means = [r['statistics']['mean'] for r in successful]
        if len(set(f"{m:.3f}" for m in all_means)) > 1:
            print("  ✅ Eye openness values are now variable (not constant)")
            print("  ✅ CognitiveLandmarkMapper integration working")
            print("  ✅ Ready for threshold calibration")
        else:
            print("  ⚠️  Still getting similar values across videos")
            print("  🔍 May need landmark index verification")
    
    print(f"\n🚀 NEXT STEPS:")
    print("  1. Verify eye landmark indices if values still seem constant")
    print("  2. Calibrate PERCLOS thresholds based on actual ranges")
    print("  3. Test with more diverse videos")
    print("  4. Compare with manual observations")


def main():
    """Main execution."""
    print("Starting Fixed Eye Calculation Test...")
    test_fixed_eye_calculation()


if __name__ == "__main__":
    main()