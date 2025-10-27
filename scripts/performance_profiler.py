#!/usr/bin/env python3
"""
Performance Profiler for Fatigue Detection System

Profiles the fatigue detection pipeline to identify bottlenecks and optimize
for real-time performance requirements (30+ fps).
"""

import sys
sys.path.append('./cognitive_overload/processing')

import time
import cProfile
import pstats
import io
from datetime import datetime
import json
import numpy as np
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
from alert_system import AlertSystem


class PerformanceProfiler:
    """
    Profiles fatigue detection system performance and identifies optimization opportunities.
    """
    
    def __init__(self):
        self.profiling_results = {}
        self.timing_data = {}
        
    def profile_full_pipeline(self, video_path: str, target_fps: float = 30.0):
        """Profile the complete fatigue detection pipeline."""
        
        print("=" * 80)
        print("⚡ PERFORMANCE PROFILING - FATIGUE DETECTION SYSTEM")
        print("=" * 80)
        print(f"Target Performance: {target_fps} fps")
        print(f"Video: {video_path}")
        
        # Initialize components
        processor = LandmarkProcessor(video_path)
        mapper = CognitiveLandmarkMapper()
        fatigue_detector = FatigueDetector()
        fatigue_detector.set_calibration('real')
        alert_system = AlertSystem()
        
        # Profile video processing
        print(f"\n📊 Profiling video processing...")
        start_time = time.time()
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Process video with timing
        video_results = processor.process_video()
        landmarks_data = video_results['landmarks_data']
        
        video_processing_time = time.time() - start_time
        profiler.disable()
        
        # Save video processing profile
        self._save_profile_stats(profiler, "video_processing")
        
        print(f"   Video processing: {video_processing_time:.2f}s for {len(landmarks_data)} frames")
        print(f"   Video processing rate: {len(landmarks_data)/video_processing_time:.1f} fps")
        
        # Profile frame-by-frame analysis
        print(f"\n📊 Profiling frame-by-frame analysis...")
        
        frame_times = []
        eye_calculation_times = []
        fatigue_update_times = []
        alert_update_times = []
        
        total_analysis_start = time.time()
        
        for i, frame_data in enumerate(landmarks_data[:100]):  # Profile first 100 frames
            if frame_data.get('face_detected', False):
                landmarks = frame_data['landmarks']
                
                # Time eye calculation
                eye_start = time.time()
                left_eye = mapper.calculate_eye_openness(landmarks, 'left')
                right_eye = mapper.calculate_eye_openness(landmarks, 'right')
                avg_openness = (left_eye + right_eye) / 2
                eye_time = time.time() - eye_start
                eye_calculation_times.append(eye_time)
                
                # Time fatigue detector update
                fatigue_start = time.time()
                timestamp = i / 30.0
                fatigue_metrics = fatigue_detector.update(avg_openness, timestamp)
                fatigue_time = time.time() - fatigue_start
                fatigue_update_times.append(fatigue_time)
                
                # Time alert system update
                alert_start = time.time()
                alert_response = alert_system.update(
                    perclos_percentage=fatigue_metrics['perclos_percentage'],
                    fatigue_level=fatigue_metrics['fatigue_level'],
                    blink_count=fatigue_metrics['blink_rate'],
                    microsleep_count=fatigue_metrics['microsleep_count'],
                    timestamp=timestamp
                )
                alert_time = time.time() - alert_start
                alert_update_times.append(alert_time)
                
                frame_total_time = eye_time + fatigue_time + alert_time
                frame_times.append(frame_total_time)
        
        total_analysis_time = time.time() - total_analysis_start
        
        # Calculate performance metrics
        self._calculate_performance_metrics(
            video_processing_time, len(landmarks_data),
            frame_times, eye_calculation_times, 
            fatigue_update_times, alert_update_times,
            total_analysis_time, target_fps
        )
        
        return self.profiling_results
    
    def _save_profile_stats(self, profiler, stage_name: str):
        """Save profiling statistics for a specific stage."""
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        profile_text = s.getvalue()
        
        # Extract key metrics
        lines = profile_text.split('\n')
        function_stats = []
        
        for line in lines:
            if 'function calls' in line:
                continue
            if line.strip() and not line.startswith(' ') and '/' in line:
                parts = line.split()
                if len(parts) >= 6:
                    function_stats.append({
                        'ncalls': parts[0],
                        'tottime': parts[1],
                        'percall': parts[2],
                        'cumtime': parts[3],
                        'percall_cum': parts[4],
                        'filename_function': ' '.join(parts[5:])
                    })
        
        self.profiling_results[stage_name] = {
            'profile_text': profile_text,
            'top_functions': function_stats[:10]
        }
    
    def _calculate_performance_metrics(self, video_time, frame_count,
                                     frame_times, eye_times, fatigue_times, 
                                     alert_times, total_time, target_fps):
        """Calculate and display performance metrics."""
        
        print(f"\n📈 PERFORMANCE ANALYSIS RESULTS:")
        
        # Video processing metrics
        video_fps = frame_count / video_time
        print(f"\n🎬 Video Processing:")
        print(f"   Total frames: {frame_count}")
        print(f"   Processing time: {video_time:.2f}s")
        print(f"   Processing rate: {video_fps:.1f} fps")
        print(f"   Target rate: {target_fps} fps")
        print(f"   Performance ratio: {video_fps/target_fps:.2f}x target")
        
        # Frame analysis metrics
        if frame_times:
            avg_frame_time = np.mean(frame_times) * 1000  # Convert to ms
            max_frame_time = np.max(frame_times) * 1000
            min_frame_time = np.min(frame_times) * 1000
            std_frame_time = np.std(frame_times) * 1000
            
            theoretical_fps = 1000 / avg_frame_time
            
            print(f"\n⚡ Frame Analysis Performance:")
            print(f"   Average frame time: {avg_frame_time:.2f}ms")
            print(f"   Min frame time: {min_frame_time:.2f}ms")
            print(f"   Max frame time: {max_frame_time:.2f}ms")
            print(f"   Std deviation: {std_frame_time:.2f}ms")
            print(f"   Theoretical max fps: {theoretical_fps:.1f} fps")
            
            # Component breakdown
            avg_eye_time = np.mean(eye_times) * 1000
            avg_fatigue_time = np.mean(fatigue_times) * 1000
            avg_alert_time = np.mean(alert_times) * 1000
            
            print(f"\n🔍 Component Breakdown (per frame):")
            print(f"   Eye calculation: {avg_eye_time:.2f}ms ({avg_eye_time/avg_frame_time*100:.1f}%)")
            print(f"   Fatigue detection: {avg_fatigue_time:.2f}ms ({avg_fatigue_time/avg_frame_time*100:.1f}%)")
            print(f"   Alert system: {avg_alert_time:.2f}ms ({avg_alert_time/avg_frame_time*100:.1f}%)")
            
            # Performance assessment
            target_frame_time = 1000 / target_fps
            print(f"\n🎯 Performance Assessment:")
            print(f"   Target frame time: {target_frame_time:.2f}ms")
            print(f"   Current avg time: {avg_frame_time:.2f}ms")
            
            if avg_frame_time <= target_frame_time:
                print(f"   Status: ✅ REAL-TIME CAPABLE")
                print(f"   Margin: {target_frame_time - avg_frame_time:.2f}ms")
            else:
                print(f"   Status: ⚠️ BELOW TARGET")
                print(f"   Deficit: {avg_frame_time - target_frame_time:.2f}ms")
            
            # Store metrics for optimization recommendations
            self.timing_data = {
                'video_fps': video_fps,
                'avg_frame_time_ms': avg_frame_time,
                'max_frame_time_ms': max_frame_time,
                'theoretical_fps': theoretical_fps,
                'target_fps': target_fps,
                'component_times': {
                    'eye_calculation_ms': avg_eye_time,
                    'fatigue_detection_ms': avg_fatigue_time,
                    'alert_system_ms': avg_alert_time
                },
                'meets_target': avg_frame_time <= target_frame_time
            }
        
        self._generate_optimization_recommendations()
    
    def _generate_optimization_recommendations(self):
        """Generate specific optimization recommendations based on profiling results."""
        
        print(f"\n🚀 OPTIMIZATION RECOMMENDATIONS:")
        
        timing = self.timing_data
        
        if timing['meets_target']:
            print(f"   ✅ System already meets {timing['target_fps']} fps target")
            print(f"   💡 Consider optimizations for edge devices or higher fps")
        else:
            deficit = timing['avg_frame_time_ms'] - (1000 / timing['target_fps'])
            print(f"   ⚠️ Need to reduce frame time by {deficit:.2f}ms")
        
        # Component-specific recommendations
        components = timing['component_times']
        slowest_component = max(components, key=components.get)
        
        print(f"\n🔧 Component-Specific Optimizations:")
        print(f"   Slowest component: {slowest_component} ({components[slowest_component]:.2f}ms)")
        
        if slowest_component == 'eye_calculation_ms':
            print(f"   Recommendations for eye calculation:")
            print(f"     • Cache landmark calculations between frames")
            print(f"     • Use vectorized numpy operations")
            print(f"     • Reduce eye landmark resolution if acceptable")
            print(f"     • Pre-compute distance calculations")
        
        elif slowest_component == 'fatigue_detection_ms':
            print(f"   Recommendations for fatigue detection:")
            print(f"     • Optimize sliding window operations")
            print(f"     • Use circular buffers instead of deque")
            print(f"     • Reduce PERCLOS calculation frequency")
            print(f"     • Cache repeated calculations")
        
        elif slowest_component == 'alert_system_ms':
            print(f"   Recommendations for alert system:")
            print(f"     • Reduce alert history buffer size")
            print(f"     • Optimize hysteresis calculations")
            print(f"     • Cache alert thresholds")
            print(f"     • Simplify escalation logic")
        
        # General optimizations
        print(f"\n⚡ General Performance Optimizations:")
        print(f"     • Use MediaPipe GPU delegation if available")
        print(f"     • Reduce face mesh resolution for faster processing")
        print(f"     • Process every nth frame for non-critical metrics")
        print(f"     • Use multi-threading for independent operations")
        print(f"     • Optimize memory allocation patterns")
        
        # Hardware recommendations
        print(f"\n💻 Hardware Recommendations:")
        if timing['avg_frame_time_ms'] > 50:
            print(f"     • Consider faster CPU for real-time processing")
            print(f"     • Use GPU acceleration for MediaPipe")
        
        if timing['theoretical_fps'] > timing['target_fps'] * 2:
            print(f"     • Current hardware exceeds requirements")
            print(f"     • Can support edge deployment")
        
        print(f"\n📊 Benchmark Results Summary:")
        print(f"     • Video processing: {timing['video_fps']:.1f} fps")
        print(f"     • Frame analysis: {timing['theoretical_fps']:.1f} fps")
        print(f"     • Target requirement: {timing['target_fps']} fps")
        print(f"     • Real-time capable: {'✅ Yes' if timing['meets_target'] else '❌ No'}")
    
    def save_profiling_report(self, filename: str = None):
        """Save comprehensive profiling report."""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_profile_{timestamp}.json'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'profiling_type': 'fatigue_detection_system',
            'performance_metrics': self.timing_data,
            'profiling_results': self.profiling_results,
            'optimization_status': 'analyzed',
            'real_time_capable': self.timing_data.get('meets_target', False)
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Performance report saved to: {filename}")
        return filename


def main():
    """Main profiling execution."""
    
    print("⚡ Starting Performance Profiling...")
    
    profiler = PerformanceProfiler()
    
    # Profile with real human face video
    video_path = './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4'
    
    try:
        results = profiler.profile_full_pipeline(video_path, target_fps=30.0)
        
        # Save profiling report
        report_file = profiler.save_profiling_report()
        
        print(f"\n✅ Performance profiling completed successfully!")
        print(f"📊 Report saved for optimization planning")
        
    except Exception as e:
        print(f"❌ Profiling error: {str(e)}")
        print("🔧 Check video path and dependencies")


if __name__ == "__main__":
    main()