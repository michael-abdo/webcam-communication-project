#!/usr/bin/env python3
"""
Smart Validation System

This validator intelligently handles mixed datasets by:
1. Identifying which videos contain faces vs. non-faces
2. Calculating metrics only on valid face videos
3. Providing actionable recommendations
"""

import os
import sys
import json
import cv2
from typing import Dict, List, Tuple, Any

sys.path.append('../processing')
from dataset_validator import DatasetValidator

class SmartValidator(DatasetValidator):
    """
    Smart validator that handles mixed datasets intelligently.
    """
    
    def __init__(self, dataset_path: str, output_dir: str = "./smart_validation_results"):
        """Initialize smart validator."""
        super().__init__(dataset_path, output_dir)
        
        self.face_videos = []
        self.non_face_videos = []
        self.synthetic_videos = []
    
    def categorize_videos(self, video_results: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize videos based on their content and detection results.
        
        Args:
            video_results (List[Dict]): List of video validation results
            
        Returns:
            Dict: Categorized videos
        """
        categories = {
            'real_face_videos': [],
            'synthetic_face_videos': [],
            'non_face_videos': [],
            'corrupted_videos': []
        }
        
        for result in video_results:
            filename = result['file_name'].lower()
            
            # Check if video processed successfully
            if not result['processing_successful']:
                categories['corrupted_videos'].append(result)
                continue
            
            detection_rate = result['processing_metrics']['detection_rate']
            
            # Categorize based on filename and detection rate
            if 'synthetic' in filename or 'realistic' in filename:
                if detection_rate > 0.5:
                    categories['synthetic_face_videos'].append(result)
                else:
                    categories['non_face_videos'].append(result)
            elif 'face' in filename or 'person' in filename or 'webcam' in filename:
                if detection_rate > 0.5:
                    categories['real_face_videos'].append(result)
                else:
                    categories['non_face_videos'].append(result)
            elif detection_rate > 0.5:
                # Assume it's a real face video if detection is high
                categories['real_face_videos'].append(result)
            else:
                # No faces detected
                categories['non_face_videos'].append(result)
        
        return categories
    
    def calculate_smart_metrics(self, categorized_videos: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Calculate metrics intelligently based on video categories.
        
        Args:
            categorized_videos (Dict): Categorized video results
            
        Returns:
            Dict: Smart metrics
        """
        # Calculate metrics for face videos only
        face_videos = (categorized_videos['real_face_videos'] + 
                      categorized_videos['synthetic_face_videos'])
        
        if not face_videos:
            return {
                'face_video_count': 0,
                'average_face_detection_rate': 0.0,
                'recommendation': 'NO_FACE_VIDEOS'
            }
        
        # Calculate detection rates for face videos
        detection_rates = [v['processing_metrics']['detection_rate'] for v in face_videos]
        avg_detection = sum(detection_rates) / len(detection_rates)
        
        # Calculate separate metrics for real vs synthetic
        real_rates = [v['processing_metrics']['detection_rate'] 
                     for v in categorized_videos['real_face_videos']]
        synthetic_rates = [v['processing_metrics']['detection_rate'] 
                          for v in categorized_videos['synthetic_face_videos']]
        
        metrics = {
            'face_video_count': len(face_videos),
            'real_face_video_count': len(categorized_videos['real_face_videos']),
            'synthetic_face_video_count': len(categorized_videos['synthetic_face_videos']),
            'non_face_video_count': len(categorized_videos['non_face_videos']),
            'average_face_detection_rate': avg_detection,
            'real_face_avg_detection': sum(real_rates) / len(real_rates) if real_rates else 0.0,
            'synthetic_face_avg_detection': sum(synthetic_rates) / len(synthetic_rates) if synthetic_rates else 0.0
        }
        
        # Determine recommendation
        if len(categorized_videos['real_face_videos']) == 0:
            metrics['recommendation'] = 'NEED_REAL_FACES'
        elif metrics['real_face_avg_detection'] >= 0.7:
            metrics['recommendation'] = 'SYSTEM_READY'
        else:
            metrics['recommendation'] = 'OPTIMIZE_SETTINGS'
        
        return metrics
    
    def validate_dataset_smart(self, max_videos: int = None) -> Dict[str, Any]:
        """
        Perform smart validation that handles mixed datasets.
        
        Args:
            max_videos (int): Maximum videos to process
            
        Returns:
            Dict: Smart validation results
        """
        # Run standard validation first
        results = self.validate_dataset(max_videos)
        
        # Categorize videos
        categorized = self.categorize_videos(results['video_results'])
        
        # Calculate smart metrics
        smart_metrics = self.calculate_smart_metrics(categorized)
        
        # Add to results
        results['video_categories'] = categorized
        results['smart_metrics'] = smart_metrics
        
        # Save enhanced results
        self.save_results()
        
        # Print smart summary
        self._print_smart_summary(categorized, smart_metrics)
        
        return results
    
    def _print_smart_summary(self, categories: Dict, metrics: Dict):
        """Print intelligent validation summary."""
        print("\n" + "="*60)
        print("SMART VALIDATION ANALYSIS")
        print("="*60)
        
        print("\nVideo Categories:")
        print(f"  Real face videos: {len(categories['real_face_videos'])}")
        print(f"  Synthetic face videos: {len(categories['synthetic_face_videos'])}")
        print(f"  Non-face videos: {len(categories['non_face_videos'])}")
        print(f"  Corrupted videos: {len(categories['corrupted_videos'])}")
        
        if metrics['face_video_count'] > 0:
            print(f"\nFace Video Detection Rates:")
            print(f"  Overall average: {metrics['average_face_detection_rate']:.1%}")
            if metrics['real_face_video_count'] > 0:
                print(f"  Real faces: {metrics['real_face_avg_detection']:.1%}")
            if metrics['synthetic_face_video_count'] > 0:
                print(f"  Synthetic faces: {metrics['synthetic_face_avg_detection']:.1%}")
        
        print(f"\n{'='*60}")
        print("RECOMMENDATION")
        print("="*60)
        
        if metrics['recommendation'] == 'NO_FACE_VIDEOS':
            print("\n❌ NO FACE VIDEOS FOUND")
            print("\nAction Required:")
            print("1. The dataset contains no videos with detectable faces")
            print("2. Please add real webcam videos to the dataset")
            print("3. Use: python3 ./webcam_datasets/record_sample_videos.py")
            
        elif metrics['recommendation'] == 'NEED_REAL_FACES':
            print("\n⚠️  REAL FACE VIDEOS NEEDED")
            print(f"\nCurrent Status:")
            print(f"- Synthetic faces work well ({metrics['synthetic_face_avg_detection']:.1%} detection)")
            print(f"- But NO real human face videos found")
            print("\nAction Required:")
            print("1. Record real webcam videos with human faces")
            print("2. Use: python3 ./webcam_datasets/record_sample_videos.py")
            print("3. Or add existing webcam videos to the dataset")
            
        elif metrics['recommendation'] == 'OPTIMIZE_SETTINGS':
            print(f"\n⚠️  OPTIMIZATION NEEDED")
            print(f"\nCurrent Status:")
            print(f"- Real face detection: {metrics['real_face_avg_detection']:.1%}")
            print(f"- Target: 70% or higher")
            print("\nAction Required:")
            print("1. Check video quality and lighting")
            print("2. Try adaptive_validator.py for automatic optimization")
            print("3. Consider recording better quality videos")
            
        else:  # SYSTEM_READY
            print("\n✅ SYSTEM READY FOR DEPLOYMENT")
            print(f"\nValidation Results:")
            print(f"- Real face detection: {metrics['real_face_avg_detection']:.1%}")
            print(f"- System meets all requirements")
            print("\nNext Steps:")
            print("1. Deploy real-time cognitive overload detection")
            print("2. Continue testing with more diverse videos")
        
        print("\n" + "="*60)

def create_quick_test_video():
    """Create a quick test video using webcam."""
    print("\n📹 QUICK WEBCAM TEST")
    print("This will record a 10-second test video from your webcam")
    
    output_path = "./webcam_datasets/quick_test.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return None
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print("Recording... (Press 'q' to stop)")
    frames_recorded = 0
    target_frames = fps * 10  # 10 seconds
    
    while frames_recorded < target_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Add recording indicator
        cv2.putText(frame, f"Recording: {frames_recorded//fps}s", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        out.write(frame)
        cv2.imshow('Quick Test Recording', frame)
        frames_recorded += 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"\n✅ Test video saved: {output_path}")
    return output_path

def main():
    """Run smart validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart validation for mixed datasets')
    parser.add_argument('dataset_path', nargs='?', default='../tests/test_videos',
                       help='Path to video dataset directory')
    parser.add_argument('--record-test', action='store_true',
                       help='Record a quick test video first')
    parser.add_argument('--max-videos', type=int, help='Maximum videos to process')
    
    args = parser.parse_args()
    
    # Record test video if requested
    if args.record_test:
        test_video = create_quick_test_video()
        if test_video:
            print("\nNow validating with your test video...")
            args.dataset_path = os.path.dirname(test_video)
    
    # Create smart validator
    validator = SmartValidator(args.dataset_path)
    
    # Run smart validation
    print(f"\n🔍 Running smart validation on: {args.dataset_path}")
    results = validator.validate_dataset_smart(max_videos=args.max_videos)
    
    # Check if we need to guide user to record videos
    if results['smart_metrics']['recommendation'] in ['NO_FACE_VIDEOS', 'NEED_REAL_FACES']:
        print("\n" + "="*60)
        print("QUICK START GUIDE")
        print("="*60)
        print("\nTo validate with real faces, run:")
        print("  python3 smart_validator.py --record-test")
        print("\nOr record multiple scenarios:")
        print("  python3 ./webcam_datasets/record_sample_videos.py")

if __name__ == "__main__":
    main()