#!/usr/bin/env python3
"""
Adaptive Validation System with Automatic Configuration Optimization

This module automatically adjusts MediaPipe settings to achieve optimal
detection rates when initial validation fails.
"""

import os
import sys
import json
import time
from typing import Dict, List, Tuple, Any

sys.path.append('../processing')
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from optimal_config import OptimalMediaPipeConfig
from dataset_validator import DatasetValidator

class AdaptiveValidator(DatasetValidator):
    """
    Enhanced validator that adapts configuration for better detection rates.
    """
    
    def __init__(self, dataset_path: str, output_dir: str = "./adaptive_validation_results"):
        """Initialize adaptive validator."""
        super().__init__(dataset_path, output_dir)
        
        # Configuration variations to try
        self.config_variations = [
            # Default optimal config
            {
                'name': 'optimal',
                'config': OptimalMediaPipeConfig.get_cognitive_overload_config()
            },
            # Lower detection threshold for challenging videos
            {
                'name': 'low_threshold',
                'config': {
                    'static_image_mode': False,
                    'max_num_faces': 1,
                    'refine_landmarks': True,
                    'min_detection_confidence': 0.5,  # Lower threshold
                    'min_tracking_confidence': 0.3    # More flexible tracking
                }
            },
            # Ultra-low threshold for maximum detection
            {
                'name': 'ultra_low_threshold',
                'config': {
                    'static_image_mode': False,
                    'max_num_faces': 1,
                    'refine_landmarks': True,
                    'min_detection_confidence': 0.3,  # Very low threshold
                    'min_tracking_confidence': 0.2    # Very flexible tracking
                }
            },
            # Static mode for difficult frames
            {
                'name': 'static_mode',
                'config': {
                    'static_image_mode': True,   # Process each frame independently
                    'max_num_faces': 1,
                    'refine_landmarks': True,
                    'min_detection_confidence': 0.5,
                    'min_tracking_confidence': 0.3
                }
            },
            # High accuracy mode
            {
                'name': 'high_accuracy',
                'config': OptimalMediaPipeConfig.get_high_accuracy_config()
            }
        ]
        
        self.adaptive_results = {
            'configurations_tested': [],
            'best_configuration': None,
            'improvement_achieved': False
        }
    
    def validate_with_adaptation(self, target_detection_rate: float = 0.7, 
                                max_videos: int = None) -> Dict[str, Any]:
        """
        Validate dataset with automatic configuration adaptation.
        
        Args:
            target_detection_rate (float): Target detection rate to achieve
            max_videos (int): Maximum videos to process
            
        Returns:
            Dict: Adaptive validation results
        """
        print(f"=== ADAPTIVE VALIDATION STARTING ===")
        print(f"Target detection rate: {target_detection_rate:.1%}")
        
        best_config = None
        best_detection_rate = 0.0
        best_results = None
        
        # Try each configuration
        for config_variant in self.config_variations:
            print(f"\n{'='*50}")
            print(f"Testing configuration: {config_variant['name']}")
            print(f"Settings: {json.dumps(config_variant['config'], indent=2)}")
            
            # Update validator config
            self.config = config_variant['config']
            
            # Reset results for new test
            self.validation_results = {
                'dataset_info': {},
                'video_results': [],
                'aggregate_metrics': {},
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Run validation
            results = self.validate_dataset(max_videos=max_videos)
            avg_detection_rate = results['aggregate_metrics']['average_detection_rate']
            
            # Track configuration performance
            config_performance = {
                'name': config_variant['name'],
                'config': config_variant['config'],
                'average_detection_rate': avg_detection_rate,
                'success_rate': results['aggregate_metrics']['success_rate']
            }
            self.adaptive_results['configurations_tested'].append(config_performance)
            
            # Check if this is the best configuration so far
            if avg_detection_rate > best_detection_rate:
                best_detection_rate = avg_detection_rate
                best_config = config_variant
                best_results = results
            
            # If we've hit our target, we can stop
            if avg_detection_rate >= target_detection_rate:
                print(f"\n✅ Target detection rate achieved: {avg_detection_rate:.1%}")
                break
        
        # Set best configuration
        self.adaptive_results['best_configuration'] = best_config
        self.adaptive_results['best_detection_rate'] = best_detection_rate
        self.adaptive_results['improvement_achieved'] = best_detection_rate >= target_detection_rate
        
        # Save adaptive results
        self._save_adaptive_results()
        
        # Print adaptive summary
        self._print_adaptive_summary(target_detection_rate)
        
        return {
            'best_results': best_results,
            'adaptive_results': self.adaptive_results,
            'success': best_detection_rate >= target_detection_rate
        }
    
    def _save_adaptive_results(self):
        """Save adaptive validation results."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"adaptive_results_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.adaptive_results, f, indent=2)
        
        print(f"\n📊 Adaptive results saved to: {output_file}")
    
    def _print_adaptive_summary(self, target_rate: float):
        """Print adaptive validation summary."""
        print("\n" + "="*60)
        print("ADAPTIVE VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\nConfigurations tested: {len(self.adaptive_results['configurations_tested'])}")
        
        print("\nResults by configuration:")
        for config_result in self.adaptive_results['configurations_tested']:
            print(f"  {config_result['name']}: {config_result['average_detection_rate']:.1%} detection")
        
        if self.adaptive_results['best_configuration']:
            print(f"\nBest configuration: {self.adaptive_results['best_configuration']['name']}")
            print(f"Best detection rate: {self.adaptive_results['best_detection_rate']:.1%}")
            
            if self.adaptive_results['improvement_achieved']:
                print(f"\n✅ SUCCESS: Achieved target detection rate of {target_rate:.1%}")
                print("\nRecommended configuration:")
                print(json.dumps(self.adaptive_results['best_configuration']['config'], indent=2))
            else:
                print(f"\n⚠️  WARNING: Could not achieve target rate of {target_rate:.1%}")
                print(f"Best achieved: {self.adaptive_results['best_detection_rate']:.1%}")
                print("\nRecommendation: Use real human face videos for proper validation")
        
        print("\n" + "="*60)

def create_optimized_config(detection_rate: float) -> Dict[str, Any]:
    """
    Create an optimized configuration based on detection performance.
    
    Args:
        detection_rate (float): Current detection rate
        
    Returns:
        Dict: Optimized MediaPipe configuration
    """
    if detection_rate >= 0.9:
        # High detection - can use stricter settings
        return {
            'static_image_mode': False,
            'max_num_faces': 1,
            'refine_landmarks': True,
            'min_detection_confidence': 0.7,
            'min_tracking_confidence': 0.5
        }
    elif detection_rate >= 0.7:
        # Good detection - balanced settings
        return {
            'static_image_mode': False,
            'max_num_faces': 1,
            'refine_landmarks': True,
            'min_detection_confidence': 0.6,
            'min_tracking_confidence': 0.4
        }
    elif detection_rate >= 0.5:
        # Moderate detection - lower thresholds
        return {
            'static_image_mode': False,
            'max_num_faces': 1,
            'refine_landmarks': True,
            'min_detection_confidence': 0.5,
            'min_tracking_confidence': 0.3
        }
    else:
        # Poor detection - minimum thresholds
        return {
            'static_image_mode': True,  # Static mode for difficult videos
            'max_num_faces': 1,
            'refine_landmarks': True,
            'min_detection_confidence': 0.3,
            'min_tracking_confidence': 0.2
        }

def main():
    """Run adaptive validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Adaptive validation with automatic optimization')
    parser.add_argument('dataset_path', help='Path to video dataset directory')
    parser.add_argument('--target-rate', type=float, default=0.7, 
                       help='Target detection rate (default: 0.7)')
    parser.add_argument('--max-videos', type=int, help='Maximum videos to process')
    
    args = parser.parse_args()
    
    # Create adaptive validator
    validator = AdaptiveValidator(args.dataset_path)
    
    # Run adaptive validation
    results = validator.validate_with_adaptation(
        target_detection_rate=args.target_rate,
        max_videos=args.max_videos
    )
    
    if results['success']:
        print("\n🎉 Validation successful with adapted configuration!")
    else:
        print("\n⚠️  Could not achieve target detection rate.")
        print("Next steps:")
        print("1. Record real human face videos using record_sample_videos.py")
        print("2. Ensure good lighting and clear face visibility")
        print("3. Re-run validation with real face videos")

if __name__ == "__main__":
    main()