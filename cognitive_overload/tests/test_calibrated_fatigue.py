#!/usr/bin/env python3
"""
Test calibrated fatigue detection with properly adjusted thresholds.
"""

import sys
sys.path.append('./cognitive_overload/processing')

from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
import numpy as np
import json
from datetime import datetime


def test_calibrated_fatigue():
    """Test fatigue detection with calibrated thresholds."""
    
    print("=" * 80)
    print("CALIBRATED FATIGUE DETECTION TEST")
    print("Testing with adjusted thresholds based on actual eye openness ranges")
    print("=" * 80)
    
    test_videos = [
        {
            'name': 'Real Human Face',
            'path': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4',
            'calibration': 'real',
            'expected_perclos': '<50% (normal alertness)'
        },
        {
            'name': 'Synthetic Neutral',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4',
            'calibration': 'synthetic',
            'expected_perclos': '<30% (neutral state)'
        },
        {
            'name': 'Synthetic Tired',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_tired.mp4',
            'calibration': 'synthetic',
            'expected_perclos': 'Should show fatigue difference'
        }
    ]
    
    results = []
    
    for test_video in test_videos:
        print(f"\n{'='*60}")
        print(f"Testing: {test_video['name']}")
        print(f"Calibration: {test_video['calibration']}")
        print(f"Expected: {test_video['expected_perclos']}")
        print(f"{'='*60}")
        
        try:
            # Initialize components
            processor = LandmarkProcessor(test_video['path'])
            mapper = CognitiveLandmarkMapper()
            fatigue_detector = FatigueDetector()
            
            # Set correct calibration
            fatigue_detector.set_calibration(test_video['calibration'])
            print(f"Eye closed threshold: {fatigue_detector.eye_closed_threshold}")
            
            # Process video  
            video_results = processor.process_video()
            landmarks_data = video_results['landmarks_data']
            
            print(f"Processing {len(landmarks_data)} frames...")
            
            # Process all frames for comprehensive PERCLOS
            eye_openness_values = []
            perclos_values = []
            
            for i, frame_data in enumerate(landmarks_data):
                if frame_data.get('face_detected', False):
                    landmarks = frame_data['landmarks']
                    
                    # Calculate eye openness
                    left_eye = mapper.calculate_eye_openness(landmarks, 'left')
                    right_eye = mapper.calculate_eye_openness(landmarks, 'right')
                    avg_openness = (left_eye + right_eye) / 2
                    
                    eye_openness_values.append(avg_openness)
                    
                    # Update fatigue detector
                    timestamp = i / 30.0  # 30fps simulation
                    metrics = fatigue_detector.update(avg_openness, timestamp)
                    perclos_values.append(metrics['perclos_percentage'])
                    
                    # Print every 30 frames (1 second)
                    if i % 30 == 0:
                        print(f"  Second {i//30:2d}: Openness={avg_openness:.3f}, PERCLOS={metrics['perclos_percentage']:.1f}%, Level={metrics['fatigue_level']}")
            
            # Calculate final statistics
            if eye_openness_values:
                final_summary = fatigue_detector.get_summary()
                
                stats = {
                    'frames_processed': len(eye_openness_values),
                    'eye_openness_mean': np.mean(eye_openness_values),
                    'eye_openness_std': np.std(eye_openness_values),
                    'eye_openness_range': (min(eye_openness_values), max(eye_openness_values)),
                    'final_perclos': final_summary['overall_perclos'],
                    'total_blinks': final_summary['total_blinks'],
                    'microsleeps': final_summary['total_microsleeps'],
                    'session_duration': final_summary['session_duration_seconds'],
                    'calibration_mode': final_summary['calibration_mode']
                }
                
                print(f"\n📊 FINAL RESULTS:")
                print(f"  Frames processed: {stats['frames_processed']}")
                print(f"  Session duration: {stats['session_duration']:.1f} seconds")
                print(f"  Eye openness: {stats['eye_openness_mean']:.3f} ± {stats['eye_openness_std']:.3f}")
                print(f"  Range: {stats['eye_openness_range'][0]:.3f} - {stats['eye_openness_range'][1]:.3f}")
                print(f"  Final PERCLOS: {stats['final_perclos']:.1f}%")
                print(f"  Total blinks: {stats['total_blinks']}")
                print(f"  Microsleeps: {stats['microsleeps']}")
                
                # Validate results
                validation = validate_perclos_results(stats, test_video)
                
                results.append({
                    'video': test_video['name'],
                    'calibration': test_video['calibration'],
                    'statistics': stats,
                    'validation': validation,
                    'status': 'success'
                })
                
            else:
                print("❌ No eye openness data collected")
                results.append({
                    'video': test_video['name'],
                    'status': 'no_data',
                    'error': 'No eye openness data'
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'video': test_video['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Save and summarize
    save_calibration_results(results)
    print_calibration_summary(results)
    
    return results


def validate_perclos_results(stats, test_video):
    """Validate PERCLOS results against expectations."""
    perclos = stats['final_perclos']
    name = test_video['name']
    
    validation = {'passed': True, 'issues': []}
    
    if 'Real Human' in name:
        # Real faces should show variable PERCLOS, not 100%
        if perclos >= 90:
            validation['passed'] = False
            validation['issues'].append(f"PERCLOS too high ({perclos:.1f}%) for real face")
        elif perclos < 10:
            validation['issues'].append(f"PERCLOS very low ({perclos:.1f}%) - possibly too alert")
        else:
            validation['issues'].append(f"PERCLOS in reasonable range ({perclos:.1f}%)")
            
    elif 'Tired' in name:
        # Tired videos should show higher PERCLOS than neutral
        validation['expected_higher_than_neutral'] = True
        validation['issues'].append(f"Tired video PERCLOS: {perclos:.1f}%")
        
    elif 'Neutral' in name:
        # Neutral should be baseline
        validation['baseline_perclos'] = perclos
        validation['issues'].append(f"Neutral baseline PERCLOS: {perclos:.1f}%")
    
    # General validation
    if 0 <= perclos <= 100:
        validation['issues'].append("PERCLOS in valid range (0-100%)")
    else:
        validation['passed'] = False
        validation['issues'].append(f"PERCLOS out of valid range: {perclos:.1f}%")
    
    return validation


def save_calibration_results(results):
    """Save calibration test results."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'calibrated_fatigue_results_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'test_type': 'calibrated_fatigue_detection',
            'results': results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")


def print_calibration_summary(results):
    """Print calibration test summary."""
    print("\n" + "="*80)
    print("CALIBRATED FATIGUE DETECTION - SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['status'] == 'success']
    
    if successful:
        print(f"\n📊 PERCLOS COMPARISON:")
        perclos_values = {}
        
        for result in successful:
            name = result['video']
            perclos = result['statistics']['final_perclos']
            calibration = result['calibration']
            threshold = "0.08" if calibration == 'real' else "0.15"
            
            print(f"  {name} ({calibration}):")
            print(f"    PERCLOS: {perclos:.1f}%")
            print(f"    Threshold: {threshold}")
            print(f"    Validation: {'✅ PASS' if result['validation']['passed'] else '❌ FAIL'}")
            
            perclos_values[name] = perclos
        
        # Compare tired vs neutral if both exist
        tired_perclos = perclos_values.get('Synthetic Tired')
        neutral_perclos = perclos_values.get('Synthetic Neutral')
        
        if tired_perclos is not None and neutral_perclos is not None:
            difference = tired_perclos - neutral_perclos
            print(f"\n🔍 TIRED vs NEUTRAL COMPARISON:")
            print(f"  Tired PERCLOS: {tired_perclos:.1f}%")
            print(f"  Neutral PERCLOS: {neutral_perclos:.1f}%")
            print(f"  Difference: {difference:+.1f}%")
            
            if difference > 5:
                print("  ✅ Tired video shows higher fatigue (good)")
            elif difference < -5:
                print("  ⚠️  Neutral video shows higher fatigue (unexpected)")
            else:
                print("  ℹ️  Similar fatigue levels (may need better test videos)")
    
    print(f"\n🎯 CALIBRATION STATUS:")
    if all(r.get('validation', {}).get('passed', False) for r in successful):
        print("  ✅ Threshold calibration successful")
        print("  ✅ PERCLOS values in reasonable ranges")
        print("  ✅ Ready for validation dataset testing")
    else:
        print("  ⚠️  Some validation issues detected")
        print("  🔧 May need threshold fine-tuning")
    
    print(f"\n🚀 NEXT STEPS:")
    print("  1. Download NTHU drowsy driver dataset")
    print("  2. Run validation against ground truth")
    print("  3. Fine-tune thresholds for >85% accuracy")
    print("  4. Implement real-time alerting")


def main():
    """Main execution."""
    print("Starting Calibrated Fatigue Detection Test...")
    test_calibrated_fatigue()


if __name__ == "__main__":
    main()