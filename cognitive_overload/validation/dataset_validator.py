#!/usr/bin/env python3
"""
Dataset Validation System for Real Face Videos

This module validates the cognitive overload detection system using
real webcam video datasets to ensure the system works with actual
human faces, not just synthetic test videos.
"""

import os
import json
import time
import glob
from typing import Dict, List, Tuple, Any
from datetime import datetime
import numpy as np
import cv2

# Import our validated components
import sys
sys.path.append('../processing')
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from optimal_config import OptimalMediaPipeConfig

class DatasetValidator:
    """
    Validates cognitive overload detection on real webcam datasets.
    """
    
    def __init__(self, dataset_path: str, output_dir: str = "./validation_results"):
        """
        Initialize the dataset validator.
        
        Args:
            dataset_path (str): Path to dataset directory
            output_dir (str): Directory for validation results
        """
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.config = OptimalMediaPipeConfig.get_cognitive_overload_config()
        self.mapper = CognitiveLandmarkMapper()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Validation metrics storage
        self.validation_results = {
            'dataset_info': {},
            'video_results': [],
            'aggregate_metrics': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def find_videos(self, extensions: List[str] = ['*.mp4', '*.avi', '*.mov']) -> List[str]:
        """
        Find all video files in the dataset directory.
        
        Args:
            extensions (List[str]): Video file extensions to search
            
        Returns:
            List[str]: Paths to video files
        """
        video_files = []
        for ext in extensions:
            pattern = os.path.join(self.dataset_path, '**', ext)
            video_files.extend(glob.glob(pattern, recursive=True))
        
        print(f"Found {len(video_files)} video files in {self.dataset_path}")
        return sorted(video_files)
    
    def validate_video(self, video_path: str) -> Dict[str, Any]:
        """
        Validate a single video file.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            Dict: Validation results for the video
        """
        print(f"\nValidating: {os.path.basename(video_path)}")
        
        results = {
            'video_path': video_path,
            'file_name': os.path.basename(video_path),
            'processing_successful': False,
            'error': None,
            'metrics': {}
        }
        
        try:
            # Initialize processor
            processor = LandmarkProcessor(video_path, self.config)
            
            # Get video metadata
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            results['video_metadata'] = {
                'fps': fps,
                'frame_count': frame_count,
                'width': width,
                'height': height,
                'duration_seconds': duration
            }
            
            # Process video with frame sampling
            # Sample every 0.5 seconds for efficiency
            frame_interval = max(1, int(fps * 0.5))
            
            start_time = time.time()
            landmarks_data = processor.process_video(frame_interval=frame_interval)
            processing_time = time.time() - start_time
            
            # Calculate performance metrics
            frames_processed = landmarks_data['metadata']['total_frames_processed']
            faces_detected = landmarks_data['metadata']['frames_with_faces']
            detection_rate = landmarks_data['metadata']['face_detection_rate']
            
            results['processing_metrics'] = {
                'processing_time': processing_time,
                'frames_processed': frames_processed,
                'faces_detected': faces_detected,
                'detection_rate': detection_rate,
                'fps_achieved': frames_processed / processing_time if processing_time > 0 else 0
            }
            
            # Calculate cognitive metrics for frames with faces
            if faces_detected > 0:
                # Handle both possible data structures
                if 'landmarks' in landmarks_data:
                    frames_data = landmarks_data['landmarks']
                elif 'landmarks_data' in landmarks_data:
                    frames_data = landmarks_data['landmarks_data']
                else:
                    frames_data = []
                
                if frames_data:
                    cognitive_metrics = self.analyze_cognitive_metrics(frames_data)
                    results['cognitive_analysis'] = cognitive_metrics
                else:
                    results['cognitive_analysis'] = {
                        'error': 'No landmark data found'
                    }
            else:
                results['cognitive_analysis'] = {
                    'error': 'No faces detected for cognitive analysis'
                }
            
            results['processing_successful'] = True
            
        except Exception as e:
            results['error'] = str(e)
            print(f"  ❌ Error: {e}")
        
        return results
    
    def analyze_cognitive_metrics(self, landmarks_frames: List[Dict]) -> Dict[str, Any]:
        """
        Analyze cognitive metrics across all frames.
        
        Args:
            landmarks_frames (List[Dict]): Landmark data for each frame
            
        Returns:
            Dict: Aggregated cognitive metrics analysis
        """
        all_metrics = []
        
        for frame_data in landmarks_frames:
            if frame_data['face_detected'] and frame_data['landmarks']:
                metrics = self.mapper.get_cognitive_metrics(frame_data['landmarks'])
                all_metrics.append(metrics)
        
        if not all_metrics:
            return {'error': 'No valid frames for analysis'}
        
        # Calculate statistics for each metric
        metric_stats = {}
        metric_names = all_metrics[0].keys()
        
        for metric_name in metric_names:
            values = [m[metric_name] for m in all_metrics]
            metric_stats[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        
        # Analyze temporal patterns
        stress_scores = [m['cognitive_stress_score'] for m in all_metrics]
        
        analysis = {
            'metric_statistics': metric_stats,
            'frame_count': len(all_metrics),
            'stress_score_trend': {
                'increasing': self._detect_trend(stress_scores, 'increasing'),
                'decreasing': self._detect_trend(stress_scores, 'decreasing'),
                'stable': self._detect_trend(stress_scores, 'stable')
            }
        }
        
        return analysis
    
    def _detect_trend(self, values: List[float], trend_type: str) -> bool:
        """
        Detect if values follow a specific trend.
        
        Args:
            values (List[float]): Time series values
            trend_type (str): 'increasing', 'decreasing', or 'stable'
            
        Returns:
            bool: Whether trend is detected
        """
        if len(values) < 3:
            return False
        
        # Simple trend detection using moving average
        window_size = min(5, len(values) // 3)
        if window_size < 2:
            return False
        
        moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')
        
        if trend_type == 'increasing':
            return moving_avg[-1] > moving_avg[0] * 1.1  # 10% increase
        elif trend_type == 'decreasing':
            return moving_avg[-1] < moving_avg[0] * 0.9  # 10% decrease
        else:  # stable
            return abs(moving_avg[-1] - moving_avg[0]) < moving_avg[0] * 0.1
    
    def validate_dataset(self, max_videos: int = None) -> Dict[str, Any]:
        """
        Validate entire dataset.
        
        Args:
            max_videos (int): Maximum number of videos to process
            
        Returns:
            Dict: Complete validation results
        """
        print(f"=== DATASET VALIDATION STARTING ===")
        print(f"Dataset path: {self.dataset_path}")
        
        # Find all videos
        video_files = self.find_videos()
        
        if not video_files:
            print("❌ No video files found!")
            return self.validation_results
        
        # Limit videos if specified
        if max_videos:
            video_files = video_files[:max_videos]
            print(f"Processing first {max_videos} videos")
        
        # Store dataset info
        self.validation_results['dataset_info'] = {
            'dataset_path': self.dataset_path,
            'total_videos_found': len(self.find_videos()),
            'videos_processed': len(video_files)
        }
        
        # Process each video
        successful_validations = 0
        total_faces_detected = 0
        total_frames_processed = 0
        all_detection_rates = []
        
        for i, video_path in enumerate(video_files):
            print(f"\nProgress: {i+1}/{len(video_files)}")
            
            # Validate video
            result = self.validate_video(video_path)
            self.validation_results['video_results'].append(result)
            
            # Update counters
            if result['processing_successful']:
                successful_validations += 1
                if 'processing_metrics' in result:
                    total_faces_detected += result['processing_metrics']['faces_detected']
                    total_frames_processed += result['processing_metrics']['frames_processed']
                    all_detection_rates.append(result['processing_metrics']['detection_rate'])
        
        # Calculate aggregate metrics
        self.validation_results['aggregate_metrics'] = {
            'successful_validations': successful_validations,
            'failed_validations': len(video_files) - successful_validations,
            'success_rate': successful_validations / len(video_files) if video_files else 0,
            'total_frames_processed': total_frames_processed,
            'total_faces_detected': total_faces_detected,
            'average_detection_rate': np.mean(all_detection_rates) if all_detection_rates else 0,
            'detection_rate_std': np.std(all_detection_rates) if all_detection_rates else 0,
            'min_detection_rate': np.min(all_detection_rates) if all_detection_rates else 0,
            'max_detection_rate': np.max(all_detection_rates) if all_detection_rates else 0
        }
        
        # Save results
        self.save_results()
        self.print_summary()
        
        return self.validation_results
    
    def save_results(self):
        """Save validation results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"validation_results_{timestamp}.json")
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                                  np.int16, np.int32, np.int64, np.uint8,
                                  np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(v) for v in obj]
            return obj
        
        # Convert results to serializable format
        serializable_results = convert_to_serializable(self.validation_results)
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📊 Results saved to: {output_file}")
    
    def print_summary(self):
        """Print validation summary."""
        metrics = self.validation_results['aggregate_metrics']
        
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        print(f"Videos processed: {self.validation_results['dataset_info']['videos_processed']}")
        print(f"Success rate: {metrics['success_rate']:.1%}")
        print(f"Average face detection rate: {metrics['average_detection_rate']:.1%}")
        print(f"Detection rate range: {metrics['min_detection_rate']:.1%} - {metrics['max_detection_rate']:.1%}")
        print(f"Total frames processed: {metrics['total_frames_processed']}")
        print(f"Total faces detected: {metrics['total_faces_detected']}")
        
        # Determine if validation passed
        validation_passed = (
            metrics['success_rate'] >= 0.9 and
            metrics['average_detection_rate'] >= 0.7
        )
        
        print("\n" + "="*50)
        if validation_passed:
            print("✅ VALIDATION PASSED - System ready for real face processing")
        else:
            print("❌ VALIDATION FAILED - System needs adjustment")
        print("="*50)

def main():
    """Run dataset validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate cognitive overload detection on webcam datasets')
    parser.add_argument('dataset_path', help='Path to video dataset directory')
    parser.add_argument('--output', default='./validation_results', help='Output directory for results')
    parser.add_argument('--max-videos', type=int, help='Maximum number of videos to process')
    
    args = parser.parse_args()
    
    # Create and run validator
    validator = DatasetValidator(args.dataset_path, args.output)
    validator.validate_dataset(max_videos=args.max_videos)

if __name__ == "__main__":
    main()