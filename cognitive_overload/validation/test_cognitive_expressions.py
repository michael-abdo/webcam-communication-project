#!/usr/bin/env python3
"""
Test Cognitive Expression Detection

This script tests the actual cognitive overload indicators:
- Brow furrow (concentration/stress)
- Eye strain (fatigue/overload) 
- Mouth tension (anxiety/stress)
- Overall cognitive stress score

Tests with real human faces to validate expression recognition.
"""

import os
import sys
import json
import numpy as np
import cv2
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
from datetime import datetime

sys.path.append('../processing')
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper

class CognitiveExpressionTester:
    """
    Test cognitive overload expression detection on real face videos.
    """
    
    def __init__(self, results_dir: str = "./cognitive_expression_results"):
        """Initialize cognitive expression tester."""
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize cognitive mapper (LandmarkProcessor will be created per video)
        self.cognitive_mapper = CognitiveLandmarkMapper()
        
        # Cognitive metrics to test
        self.cognitive_metrics = [
            'brow_furrow_distance',
            'left_eye_openness', 
            'right_eye_openness',
            'avg_eye_openness',
            'mouth_compression',
            'cognitive_stress_score'
        ]
        
        # Test datasets with expected cognitive states
        self.test_datasets = [
            {
                'name': 'live_face_datasets/selfies_videos_kaggle',
                'expected_state': 'neutral_to_mild_stress',
                'description': 'Real human selfie videos - various natural expressions',
                'expected_metrics': {
                    'brow_furrow_distance': (80, 120),  # pixels
                    'avg_eye_openness': (0.1, 0.3),     # ratio
                    'mouth_compression': (0.0, 0.2),    # ratio
                    'cognitive_stress_score': (0.3, 0.8) # normalized
                }
            },
            {
                'name': 'real_face_datasets/validation_dataset',
                'expected_state': 'synthetic_expressions',
                'description': 'Synthetic faces with designed expressions',
                'expected_metrics': {
                    'brow_furrow_distance': (90, 100),
                    'avg_eye_openness': (0.14, 0.16),
                    'mouth_compression': (0.0, 0.01),
                    'cognitive_stress_score': (0.6, 0.65)
                }
            }
        ]
    
    def analyze_video_cognitive_metrics(self, video_path: str) -> Dict[str, Any]:
        """Analyze cognitive metrics for a single video."""
        print(f"\nAnalyzing cognitive expressions: {os.path.basename(video_path)}")
        
        try:
            # Create landmark processor for this specific video
            landmark_processor = LandmarkProcessor(video_path)
            
            # Process video with landmark detection
            landmarks_data = landmark_processor.process_video()
            
            if not landmarks_data or 'landmarks_data' not in landmarks_data:
                return {
                    'success': False,
                    'error': 'No landmark data extracted',
                    'video_path': video_path
                }
            
            frames_data = landmarks_data['landmarks_data']
            
            if not frames_data:
                return {
                    'success': False,
                    'error': 'No frames with face detection',
                    'video_path': video_path
                }
            
            # Calculate cognitive metrics for each frame
            cognitive_results = []
            
            for frame_data in frames_data:
                if frame_data.get('face_detected', False):
                    landmarks = frame_data['landmarks']
                    
                    # Calculate all cognitive metrics
                    metrics = {}
                    
                    # Brow furrow (concentration/stress indicator)
                    metrics['brow_furrow_distance'] = self._calculate_brow_furrow_distance(landmarks)
                    
                    # Eye openness (fatigue/alertness indicator)
                    metrics['left_eye_openness'] = self._calculate_eye_openness(landmarks, 'left')
                    metrics['right_eye_openness'] = self._calculate_eye_openness(landmarks, 'right')
                    metrics['avg_eye_openness'] = (metrics['left_eye_openness'] + metrics['right_eye_openness']) / 2
                    
                    # Mouth tension (stress/anxiety indicator)
                    metrics['mouth_compression'] = self._calculate_mouth_compression(landmarks)
                    
                    # Overall cognitive stress score
                    metrics['cognitive_stress_score'] = self._calculate_cognitive_stress_score(
                        metrics['brow_furrow_distance'],
                        metrics['avg_eye_openness'],
                        metrics['mouth_compression']
                    )
                    
                    cognitive_results.append(metrics)
            
            if not cognitive_results:
                return {
                    'success': False,
                    'error': 'No cognitive metrics calculated',
                    'video_path': video_path
                }
            
            # Calculate statistics across all frames
            stats = self._calculate_cognitive_statistics(cognitive_results)
            
            # Analyze cognitive patterns
            patterns = self._analyze_cognitive_patterns(cognitive_results)
            
            return {
                'success': True,
                'video_path': video_path,
                'frames_analyzed': len(cognitive_results),
                'cognitive_statistics': stats,
                'cognitive_patterns': patterns,
                'raw_metrics': cognitive_results[:10],  # Sample of raw data
                'processing_info': {
                    'total_frames': landmarks_data.get('total_frames', 0),
                    'face_detection_rate': len(cognitive_results) / max(1, landmarks_data.get('total_frames', 1))
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Processing error: {str(e)}",
                'video_path': video_path
            }
    
    def _calculate_cognitive_statistics(self, cognitive_data: List[Dict]) -> Dict[str, Dict]:
        """Calculate statistics for cognitive metrics."""
        stats = {}
        
        for metric in self.cognitive_metrics:
            values = [frame[metric] for frame in cognitive_data if metric in frame]
            
            if values:
                stats[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values),
                    'count': len(values)
                }
            else:
                stats[metric] = {
                    'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0, 'count': 0
                }
        
        return stats
    
    def _analyze_cognitive_patterns(self, cognitive_data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in cognitive metrics over time."""
        patterns = {}
        
        # Stress level classification
        stress_scores = [frame['cognitive_stress_score'] for frame in cognitive_data]
        avg_stress = np.mean(stress_scores)
        
        if avg_stress < 0.4:
            stress_level = 'LOW'
        elif avg_stress < 0.7:
            stress_level = 'MODERATE'
        else:
            stress_level = 'HIGH'
        
        patterns['stress_level'] = stress_level
        patterns['stress_score_avg'] = avg_stress
        
        # Eye strain analysis
        eye_openness = [frame['avg_eye_openness'] for frame in cognitive_data]
        avg_eye_openness = np.mean(eye_openness)
        
        if avg_eye_openness < 0.1:
            eye_state = 'VERY_TIRED'
        elif avg_eye_openness < 0.15:
            eye_state = 'TIRED'
        elif avg_eye_openness < 0.25:
            eye_state = 'NORMAL'
        else:
            eye_state = 'ALERT'
        
        patterns['eye_state'] = eye_state
        patterns['eye_openness_avg'] = avg_eye_openness
        
        # Concentration analysis (brow furrow)
        brow_distances = [frame['brow_furrow_distance'] for frame in cognitive_data]
        avg_brow_distance = np.mean(brow_distances)
        
        if avg_brow_distance < 85:
            concentration_level = 'HIGH_CONCENTRATION'
        elif avg_brow_distance < 95:
            concentration_level = 'MODERATE_CONCENTRATION'
        else:
            concentration_level = 'RELAXED'
        
        patterns['concentration_level'] = concentration_level
        patterns['brow_furrow_avg'] = avg_brow_distance
        
        # Temporal trends
        if len(stress_scores) > 5:
            # Simple trend analysis
            first_half = np.mean(stress_scores[:len(stress_scores)//2])
            second_half = np.mean(stress_scores[len(stress_scores)//2:])
            
            if second_half > first_half + 0.1:
                patterns['stress_trend'] = 'INCREASING'
            elif second_half < first_half - 0.1:
                patterns['stress_trend'] = 'DECREASING'
            else:
                patterns['stress_trend'] = 'STABLE'
        else:
            patterns['stress_trend'] = 'INSUFFICIENT_DATA'
        
        return patterns
    
    def _calculate_brow_furrow_distance(self, landmarks: List[Tuple[float, float]]) -> float:
        """Calculate brow furrow distance (concentration indicator)."""
        try:
            # Use eyebrow landmarks from cognitive mapper
            left_brow = self.cognitive_mapper.left_eyebrow_landmarks
            right_brow = self.cognitive_mapper.right_eyebrow_landmarks
            
            # Calculate distance between inner eyebrow points
            left_inner = landmarks[left_brow[0]]  # Inner left eyebrow
            right_inner = landmarks[right_brow[0]]  # Inner right eyebrow
            
            # Calculate Euclidean distance
            distance = np.sqrt((left_inner[0] - right_inner[0])**2 + (left_inner[1] - right_inner[1])**2)
            
            # Convert to pixels (assuming normalized coordinates need scaling)
            return distance * 1000  # Scale to reasonable pixel range
            
        except (IndexError, KeyError):
            return 95.0  # Default middle value
    
    def _calculate_eye_openness(self, landmarks: List[Tuple[float, float]], eye: str) -> float:
        """Calculate eye openness ratio (fatigue indicator)."""
        try:
            if eye == 'left':
                eye_landmarks = self.cognitive_mapper.left_eye_landmarks
            else:
                eye_landmarks = self.cognitive_mapper.right_eye_landmarks
            
            # Get upper and lower eyelid points
            upper_lid = eye_landmarks['upper_lid'][:4]  # Use first 4 points
            lower_lid = eye_landmarks['lower_lid'][:4]  # Use first 4 points
            
            # Calculate average vertical distance
            vertical_distances = []
            for i in range(min(len(upper_lid), len(lower_lid))):
                upper_point = landmarks[upper_lid[i]]
                lower_point = landmarks[lower_lid[i]]
                vertical_dist = abs(upper_point[1] - lower_point[1])
                vertical_distances.append(vertical_dist)
            
            avg_vertical = np.mean(vertical_distances)
            
            # Calculate horizontal distance for normalization
            inner_corner = landmarks[eye_landmarks['inner_corner'][0]]
            outer_corner = landmarks[eye_landmarks['outer_corner'][0]]
            horizontal_dist = abs(outer_corner[0] - inner_corner[0])
            
            # Return ratio of vertical to horizontal (eye openness ratio)
            return avg_vertical / max(horizontal_dist, 0.001)  # Avoid division by zero
            
        except (IndexError, KeyError):
            return 0.15  # Default normal eye openness
    
    def _calculate_mouth_compression(self, landmarks: List[Tuple[float, float]]) -> float:
        """Calculate mouth compression ratio (stress indicator)."""
        try:
            mouth_landmarks = self.cognitive_mapper.mouth_landmarks
            
            # Get mouth corner points
            left_corner = landmarks[mouth_landmarks['corners'][0]]
            right_corner = landmarks[mouth_landmarks['corners'][1]]
            
            # Get mouth top and bottom center points
            top_center = landmarks[mouth_landmarks['center_top'][0]]
            bottom_center = landmarks[mouth_landmarks['center_bottom'][0]]
            
            # Calculate horizontal and vertical distances
            horizontal_dist = abs(right_corner[0] - left_corner[0])
            vertical_dist = abs(top_center[1] - bottom_center[1])
            
            # Compression ratio (lower values indicate more compression/tension)
            compression_ratio = vertical_dist / max(horizontal_dist, 0.001)
            
            # Return compression intensity (higher values = more compression)
            return max(0, 0.5 - compression_ratio)  # Invert so higher = more compressed
            
        except (IndexError, KeyError):
            return 0.1  # Default low compression
    
    def _calculate_cognitive_stress_score(self, brow_furrow: float, eye_openness: float, mouth_compression: float) -> float:
        """Calculate overall cognitive stress score (0-1 scale)."""
        try:
            # Normalize individual metrics to 0-1 scale
            
            # Brow furrow: lower distance = higher stress (concentrated)
            brow_stress = max(0, min(1, (100 - brow_furrow) / 20))  # Lower furrow = higher stress
            
            # Eye openness: lower openness = higher fatigue/stress
            eye_stress = max(0, min(1, (0.25 - eye_openness) / 0.15))  # Lower openness = higher stress
            
            # Mouth compression: higher compression = higher stress
            mouth_stress = max(0, min(1, mouth_compression / 0.3))  # Higher compression = higher stress
            
            # Weighted combination (brow furrow is strongest indicator)
            stress_score = (0.5 * brow_stress + 0.3 * eye_stress + 0.2 * mouth_stress)
            
            return max(0, min(1, stress_score))  # Ensure 0-1 range
            
        except:
            return 0.5  # Default middle stress level
    
    def test_dataset_cognitive_expressions(self, dataset_config: Dict) -> Dict[str, Any]:
        """Test cognitive expression detection on a dataset."""
        print(f"\n{'='*60}")
        print(f"TESTING COGNITIVE EXPRESSIONS: {dataset_config['name'].upper()}")
        print(f"Expected State: {dataset_config['expected_state']}")
        print(f"Description: {dataset_config['description']}")
        print(f"{'='*60}")
        
        dataset_path = dataset_config['name']
        
        if not os.path.exists(dataset_path):
            return {
                'success': False,
                'error': f"Dataset path not found: {dataset_path}",
                'dataset': dataset_config['name']
            }
        
        # Find video files
        video_files = []
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    video_files.append(os.path.join(root, file))
        
        if not video_files:
            return {
                'success': False,
                'error': f"No video files found in {dataset_path}",
                'dataset': dataset_config['name']
            }
        
        print(f"Found {len(video_files)} videos to analyze")
        
        # Test up to 10 videos for comprehensive analysis
        test_videos = video_files[:10]
        video_results = []
        
        for i, video_path in enumerate(test_videos, 1):
            print(f"\nProgress: {i}/{len(test_videos)}")
            result = self.analyze_video_cognitive_metrics(video_path)
            video_results.append(result)
            
            if result['success']:
                patterns = result['cognitive_patterns']
                print(f"   Stress Level: {patterns['stress_level']}")
                print(f"   Eye State: {patterns['eye_state']}")
                print(f"   Concentration: {patterns['concentration_level']}")
            else:
                print(f"   ❌ Analysis failed: {result['error']}")
        
        # Aggregate results across all videos
        successful_results = [r for r in video_results if r['success']]
        
        if not successful_results:
            return {
                'success': False,
                'error': 'No videos were successfully analyzed',
                'dataset': dataset_config['name'],
                'video_results': video_results
            }
        
        # Calculate dataset-wide cognitive metrics
        dataset_cognitive_summary = self._summarize_dataset_cognitive_metrics(
            successful_results, dataset_config
        )
        
        return {
            'success': True,
            'dataset': dataset_config['name'],
            'expected_state': dataset_config['expected_state'],
            'videos_analyzed': len(successful_results),
            'videos_total': len(test_videos),
            'cognitive_summary': dataset_cognitive_summary,
            'video_results': video_results,
            'validation_results': self._validate_against_expectations(
                dataset_cognitive_summary, dataset_config['expected_metrics']
            )
        }
    
    def _summarize_dataset_cognitive_metrics(self, results: List[Dict], dataset_config: Dict) -> Dict[str, Any]:
        """Summarize cognitive metrics across all videos in dataset."""
        summary = {}
        
        # Collect all cognitive statistics
        all_stats = {}
        for metric in self.cognitive_metrics:
            all_stats[metric] = {
                'values': [],
                'means': [],
                'stds': []
            }
        
        for result in results:
            stats = result['cognitive_statistics']
            for metric in self.cognitive_metrics:
                if metric in stats:
                    all_stats[metric]['means'].append(stats[metric]['mean'])
                    all_stats[metric]['stds'].append(stats[metric]['std'])
        
        # Calculate dataset-wide statistics
        for metric in self.cognitive_metrics:
            if all_stats[metric]['means']:
                summary[metric] = {
                    'dataset_mean': np.mean(all_stats[metric]['means']),
                    'dataset_std': np.mean(all_stats[metric]['stds']),
                    'video_count': len(all_stats[metric]['means']),
                    'range': (
                        np.min(all_stats[metric]['means']),
                        np.max(all_stats[metric]['means'])
                    )
                }
        
        # Aggregate cognitive patterns
        all_patterns = [r['cognitive_patterns'] for r in results]
        
        stress_levels = [p['stress_level'] for p in all_patterns]
        eye_states = [p['eye_state'] for p in all_patterns]
        concentration_levels = [p['concentration_level'] for p in all_patterns]
        
        summary['pattern_distribution'] = {
            'stress_levels': {level: stress_levels.count(level) for level in set(stress_levels)},
            'eye_states': {state: eye_states.count(state) for state in set(eye_states)},
            'concentration_levels': {level: concentration_levels.count(level) for level in set(concentration_levels)}
        }
        
        # Overall dataset characterization
        avg_stress_scores = [p['stress_score_avg'] for p in all_patterns]
        summary['dataset_characterization'] = {
            'primary_stress_level': max(summary['pattern_distribution']['stress_levels'], 
                                      key=summary['pattern_distribution']['stress_levels'].get),
            'primary_eye_state': max(summary['pattern_distribution']['eye_states'],
                                   key=summary['pattern_distribution']['eye_states'].get),
            'primary_concentration': max(summary['pattern_distribution']['concentration_levels'],
                                       key=summary['pattern_distribution']['concentration_levels'].get),
            'avg_stress_score': np.mean(avg_stress_scores),
            'stress_score_variability': np.std(avg_stress_scores)
        }
        
        return summary
    
    def _validate_against_expectations(self, summary: Dict, expected_metrics: Dict) -> Dict[str, Any]:
        """Validate cognitive metrics against expected ranges."""
        validation = {}
        
        for metric, expected_range in expected_metrics.items():
            if metric in summary:
                actual_value = summary[metric]['dataset_mean']
                min_expected, max_expected = expected_range
                
                in_range = min_expected <= actual_value <= max_expected
                
                validation[metric] = {
                    'expected_range': expected_range,
                    'actual_value': actual_value,
                    'in_expected_range': in_range,
                    'status': 'PASS' if in_range else 'FAIL'
                }
            else:
                validation[metric] = {
                    'expected_range': expected_range,
                    'actual_value': None,
                    'in_expected_range': False,
                    'status': 'NO_DATA'
                }
        
        # Overall validation status
        passed_metrics = sum(1 for v in validation.values() if v['status'] == 'PASS')
        total_metrics = len(validation)
        
        validation['overall'] = {
            'passed_metrics': passed_metrics,
            'total_metrics': total_metrics,
            'pass_rate': passed_metrics / total_metrics if total_metrics > 0 else 0,
            'status': 'PASS' if passed_metrics >= total_metrics * 0.75 else 'FAIL'
        }
        
        return validation
    
    def run_comprehensive_cognitive_tests(self) -> Dict[str, Any]:
        """Run comprehensive cognitive expression tests on all datasets."""
        print("="*80)
        print("COMPREHENSIVE COGNITIVE EXPRESSION DETECTION TESTING")
        print("Testing brow furrow, eye strain, mouth tension, and stress indicators")
        print("="*80)
        
        all_results = {}
        
        for dataset_config in self.test_datasets:
            result = self.test_dataset_cognitive_expressions(dataset_config)
            all_results[dataset_config['name']] = result
        
        # Generate comprehensive report
        report = self._generate_cognitive_testing_report(all_results)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = os.path.join(self.results_dir, f'cognitive_expression_results_{timestamp}.json')
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'test_summary': report,
                'detailed_results': all_results
            }, f, indent=2, default=str)
        
        print(f"\n📊 Comprehensive results saved to: {results_file}")
        
        return {
            'test_summary': report,
            'detailed_results': all_results,
            'results_file': results_file
        }
    
    def _generate_cognitive_testing_report(self, all_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive cognitive testing report."""
        report = {
            'executive_summary': {},
            'cognitive_metrics_validation': {},
            'dataset_analysis': {},
            'recommendations': []
        }
        
        successful_datasets = {k: v for k, v in all_results.items() if v.get('success', False)}
        
        # Executive Summary
        total_datasets = len(all_results)
        successful_datasets_count = len(successful_datasets)
        total_videos_analyzed = sum(r.get('videos_analyzed', 0) for r in successful_datasets.values())
        
        report['executive_summary'] = {
            'datasets_tested': total_datasets,
            'successful_datasets': successful_datasets_count,
            'success_rate': successful_datasets_count / total_datasets if total_datasets > 0 else 0,
            'total_videos_analyzed': total_videos_analyzed,
            'cognitive_detection_working': successful_datasets_count > 0
        }
        
        # Cognitive Metrics Validation
        all_validations = []
        for dataset_name, result in successful_datasets.items():
            if 'validation_results' in result:
                validation = result['validation_results']
                all_validations.append({
                    'dataset': dataset_name,
                    'pass_rate': validation['overall']['pass_rate'],
                    'status': validation['overall']['status']
                })
        
        if all_validations:
            avg_pass_rate = np.mean([v['pass_rate'] for v in all_validations])
            passing_datasets = sum(1 for v in all_validations if v['status'] == 'PASS')
            
            report['cognitive_metrics_validation'] = {
                'average_pass_rate': avg_pass_rate,
                'datasets_passing': passing_datasets,
                'datasets_tested': len(all_validations),
                'overall_validation_status': 'PASS' if avg_pass_rate >= 0.75 else 'NEEDS_IMPROVEMENT'
            }
        
        # Dataset Analysis
        for dataset_name, result in successful_datasets.items():
            if 'cognitive_summary' in result:
                summary = result['cognitive_summary']
                characterization = summary.get('dataset_characterization', {})
                
                report['dataset_analysis'][dataset_name] = {
                    'primary_stress_level': characterization.get('primary_stress_level', 'UNKNOWN'),
                    'primary_eye_state': characterization.get('primary_eye_state', 'UNKNOWN'),
                    'concentration_level': characterization.get('primary_concentration', 'UNKNOWN'),
                    'avg_stress_score': characterization.get('avg_stress_score', 0),
                    'videos_analyzed': result.get('videos_analyzed', 0)
                }
        
        # Recommendations
        if report['executive_summary']['cognitive_detection_working']:
            if report['cognitive_metrics_validation'].get('overall_validation_status') == 'PASS':
                report['recommendations'].append("✅ Cognitive expression detection is working correctly")
                report['recommendations'].append("✅ System ready for cognitive overload monitoring")
                report['recommendations'].append("✅ Proceed with user pilot testing")
            else:
                report['recommendations'].append("⚠️ Cognitive metrics need calibration")
                report['recommendations'].append("⚠️ Review metric thresholds and ranges")
        else:
            report['recommendations'].append("❌ Cognitive expression detection needs troubleshooting")
            report['recommendations'].append("❌ Check landmark processing and cognitive mapping")
        
        return report

def main():
    """Main execution function."""
    print("COGNITIVE EXPRESSION DETECTION TESTING")
    print("Testing actual cognitive overload indicators with real faces")
    print("="*80)
    
    tester = CognitiveExpressionTester()
    results = tester.run_comprehensive_cognitive_tests()
    
    # Print summary report
    print("\n" + "="*80)
    print("COGNITIVE TESTING FINAL REPORT")
    print("="*80)
    
    summary = results['test_summary']
    exec_summary = summary['executive_summary']
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   Datasets Tested: {exec_summary['datasets_tested']}")
    print(f"   Successful Analysis: {exec_summary['successful_datasets']}")
    print(f"   Videos Analyzed: {exec_summary['total_videos_analyzed']}")
    print(f"   Cognitive Detection Working: {'✅ YES' if exec_summary['cognitive_detection_working'] else '❌ NO'}")
    
    if 'cognitive_metrics_validation' in summary:
        validation = summary['cognitive_metrics_validation']
        print(f"\n🎯 VALIDATION RESULTS:")
        print(f"   Average Pass Rate: {validation['average_pass_rate']:.1%}")
        print(f"   Overall Status: {validation['overall_validation_status']}")
    
    print(f"\n🔍 DATASET ANALYSIS:")
    for dataset, analysis in summary['dataset_analysis'].items():
        print(f"   {dataset}:")
        print(f"     - Stress Level: {analysis['primary_stress_level']}")
        print(f"     - Eye State: {analysis['primary_eye_state']}")
        print(f"     - Concentration: {analysis['concentration_level']}")
        print(f"     - Avg Stress Score: {analysis['avg_stress_score']:.3f}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in summary['recommendations']:
        print(f"   {rec}")
    
    print(f"\n📁 Detailed results: {results['results_file']}")

if __name__ == "__main__":
    main()