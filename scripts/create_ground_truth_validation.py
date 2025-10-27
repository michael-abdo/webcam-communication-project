#!/usr/bin/env python3
"""
Create Ground Truth Validation Dataset

Creates a manually labeled ground truth dataset from our existing videos
for immediate validation of the fatigue detection system.
"""

import sys
sys.path.append('./cognitive_overload/processing')

import os
import json
import glob
from datetime import datetime
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector


def create_ground_truth_dataset():
    """Create ground truth validation dataset from existing videos."""
    
    print("=" * 80)
    print("CREATING GROUND TRUTH VALIDATION DATASET")
    print("=" * 80)
    
    # Define test videos with manual ground truth labels
    test_videos = [
        {
            'name': 'Real Human Face 1',
            'path': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4',
            'type': 'real',
            'expected_fatigue': 'alert',  # Manual observation: person appears alert
            'expected_perclos_range': (0, 10),  # Expected PERCLOS percentage
            'description': 'Young person looking at camera, appears alert and engaged'
        },
        {
            'name': 'Real Human Face 2', 
            'path': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/4.mp4',
            'type': 'real',
            'expected_fatigue': 'alert',
            'expected_perclos_range': (0, 10),
            'description': 'Another person appearing alert'
        },
        {
            'name': 'Real Human Face 3',
            'path': './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/2/3.mp4', 
            'type': 'real',
            'expected_fatigue': 'alert',
            'expected_perclos_range': (0, 10),
            'description': 'Third person appearing alert'
        },
        {
            'name': 'Synthetic Neutral Baseline',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4',
            'type': 'synthetic',
            'expected_fatigue': 'alert',
            'expected_perclos_range': (0, 5),
            'description': 'Synthetic face in neutral state, should show minimal fatigue'
        },
        {
            'name': 'Synthetic Tired State',
            'path': './cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_tired.mp4',
            'type': 'synthetic', 
            'expected_fatigue': 'mild_fatigue',
            'expected_perclos_range': (10, 30),
            'description': 'Synthetic face showing tired expressions, should show elevated fatigue'
        }
    ]
    
    validation_results = []
    
    for video_config in test_videos:
        print(f"\n{'='*60}")
        print(f"Processing: {video_config['name']}")
        print(f"Expected: {video_config['expected_fatigue']} ({video_config['expected_perclos_range'][0]}-{video_config['expected_perclos_range'][1]}% PERCLOS)")
        print(f"{'='*60}")
        
        if not os.path.exists(video_config['path']):
            print(f"❌ Video not found: {video_config['path']}")
            continue
            
        try:
            # Initialize components
            processor = LandmarkProcessor(video_config['path'])
            mapper = CognitiveLandmarkMapper()
            fatigue_detector = FatigueDetector()
            
            # Set calibration based on video type
            fatigue_detector.set_calibration(video_config['type'])
            
            # Process video
            video_results = processor.process_video()
            landmarks_data = video_results['landmarks_data']
            
            print(f"Processing {len(landmarks_data)} frames...")
            
            # Calculate fatigue metrics
            eye_openness_values = []
            
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
                    fatigue_detector.update(avg_openness, timestamp)
            
            # Get final results
            if eye_openness_values:
                final_summary = fatigue_detector.get_summary()
                final_metrics = fatigue_detector._calculate_metrics()
                
                # Calculate validation accuracy
                actual_perclos = final_summary['overall_perclos']
                expected_range = video_config['expected_perclos_range']
                
                perclos_accurate = expected_range[0] <= actual_perclos <= expected_range[1]
                fatigue_level_accurate = validate_fatigue_level(
                    final_metrics['fatigue_level'], 
                    video_config['expected_fatigue']
                )
                
                result = {
                    'video_name': video_config['name'],
                    'video_path': video_config['path'],
                    'video_type': video_config['type'],
                    'ground_truth': {
                        'expected_fatigue': video_config['expected_fatigue'],
                        'expected_perclos_range': video_config['expected_perclos_range'],
                        'description': video_config['description']
                    },
                    'measured_results': {
                        'perclos_percentage': actual_perclos,
                        'fatigue_level': final_metrics['fatigue_level'],
                        'blink_count': final_summary['total_blinks'],
                        'session_duration': final_summary['session_duration_seconds'],
                        'eye_openness_mean': float(sum(eye_openness_values) / len(eye_openness_values)),
                        'eye_openness_std': float(
                            (sum((x - sum(eye_openness_values)/len(eye_openness_values))**2 for x in eye_openness_values) / len(eye_openness_values))**0.5
                        )
                    },
                    'validation': {
                        'perclos_accurate': perclos_accurate,
                        'fatigue_level_accurate': fatigue_level_accurate,
                        'overall_accurate': perclos_accurate and fatigue_level_accurate,
                        'perclos_error': actual_perclos - ((expected_range[0] + expected_range[1]) / 2),
                        'notes': []
                    }
                }
                
                # Add validation notes
                if not perclos_accurate:
                    result['validation']['notes'].append(
                        f"PERCLOS {actual_perclos:.1f}% outside expected range {expected_range[0]}-{expected_range[1]}%"
                    )
                
                if not fatigue_level_accurate:
                    result['validation']['notes'].append(
                        f"Fatigue level '{final_metrics['fatigue_level']}' doesn't match expected '{video_config['expected_fatigue']}'"
                    )
                
                if result['validation']['overall_accurate']:
                    result['validation']['notes'].append("✅ All validation criteria met")
                
                validation_results.append(result)
                
                print(f"✅ Results:")
                print(f"  PERCLOS: {actual_perclos:.1f}% (expected: {expected_range[0]}-{expected_range[1]}%)")
                print(f"  Fatigue Level: {final_metrics['fatigue_level']} (expected: {video_config['expected_fatigue']})")
                print(f"  Validation: {'✅ PASS' if result['validation']['overall_accurate'] else '❌ FAIL'}")
                
            else:
                print(f"❌ No face detection data for {video_config['name']}")
                
        except Exception as e:
            print(f"❌ Error processing {video_config['name']}: {str(e)}")
            validation_results.append({
                'video_name': video_config['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Save ground truth validation results
    save_ground_truth_results(validation_results)
    calculate_overall_accuracy(validation_results)
    
    return validation_results


def validate_fatigue_level(actual: str, expected: str) -> bool:
    """Validate if fatigue level matches expectation."""
    # Create fatigue level hierarchy
    fatigue_hierarchy = {
        'alert': 0,
        'mild_fatigue': 1, 
        'drowsy': 2,
        'severe_fatigue': 3
    }
    
    # Map expected to actual with some tolerance
    expected_lower = expected.lower().replace(' ', '_')
    actual_lower = actual.lower().replace(' ', '_')
    
    if expected_lower not in fatigue_hierarchy or actual_lower not in fatigue_hierarchy:
        return False
    
    expected_level = fatigue_hierarchy[expected_lower]
    actual_level = fatigue_hierarchy[actual_lower]
    
    # Allow ±1 level tolerance (e.g., alert can be mild_fatigue, mild can be alert or drowsy)
    return abs(actual_level - expected_level) <= 1


def save_ground_truth_results(results):
    """Save ground truth validation results."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'ground_truth_validation_{timestamp}.json'
    
    output = {
        'timestamp': timestamp,
        'test_type': 'ground_truth_validation',
        'total_videos': len(results),
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 Ground truth validation saved to: {filename}")


def calculate_overall_accuracy(results):
    """Calculate and display overall validation accuracy."""
    
    successful_results = [r for r in results if 'validation' in r]
    if not successful_results:
        print("\n❌ No successful validation results")
        return
    
    total_tests = len(successful_results)
    perclos_accurate = sum(1 for r in successful_results if r['validation']['perclos_accurate'])
    fatigue_accurate = sum(1 for r in successful_results if r['validation']['fatigue_level_accurate'])
    overall_accurate = sum(1 for r in successful_results if r['validation']['overall_accurate'])
    
    print(f"\n" + "="*80)
    print("GROUND TRUTH VALIDATION SUMMARY")
    print("="*80)
    
    print(f"\n📊 ACCURACY METRICS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  PERCLOS Accuracy: {perclos_accurate}/{total_tests} ({perclos_accurate/total_tests*100:.1f}%)")
    print(f"  Fatigue Level Accuracy: {fatigue_accurate}/{total_tests} ({fatigue_accurate/total_tests*100:.1f}%)")
    print(f"  Overall Accuracy: {overall_accurate}/{total_tests} ({overall_accurate/total_tests*100:.1f}%)")
    
    target_accuracy = 85.0
    overall_percentage = overall_accurate/total_tests*100
    
    print(f"\n🎯 TARGET VALIDATION:")
    print(f"  Target Accuracy: {target_accuracy}%")
    print(f"  Achieved Accuracy: {overall_percentage:.1f}%")
    
    if overall_percentage >= target_accuracy:
        print(f"  ✅ TARGET ACHIEVED - Ready for production!")
    else:
        print(f"  ⚠️  Below target by {target_accuracy - overall_percentage:.1f}%")
        print(f"  🔧 Recommendations:")
        print(f"     - Fine-tune PERCLOS thresholds")
        print(f"     - Expand ground truth dataset")
        print(f"     - Test with more diverse face types")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in successful_results:
        status = "✅ PASS" if result['validation']['overall_accurate'] else "❌ FAIL"
        perclos = result['measured_results']['perclos_percentage']
        fatigue = result['measured_results']['fatigue_level']
        print(f"  {result['video_name']}: {status}")
        print(f"    PERCLOS: {perclos:.1f}%, Fatigue: {fatigue}")
        if result['validation']['notes']:
            for note in result['validation']['notes']:
                print(f"    Note: {note}")


def main():
    """Main execution."""
    print("Creating Ground Truth Validation Dataset...")
    create_ground_truth_dataset()


if __name__ == "__main__":
    main()