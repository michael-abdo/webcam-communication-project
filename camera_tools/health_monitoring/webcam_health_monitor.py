#!/usr/bin/env python3
"""
Webcam Health Monitor
Comprehensive camera health monitoring and diagnostics tool
"""

import cv2
import time
import json
import platform
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WebcamHealthMonitor:
    """Monitor webcam health, status, and performance metrics."""
    
    def __init__(self):
        self.camera_index = 0
        self.camera = None
        self.health_history = []
        self.start_time = time.time()
        
    def enumerate_cameras(self) -> List[Dict]:
        """Enumerate all available cameras on the system."""
        cameras = []
        
        # Check up to 10 camera indices
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                cameras.append({
                    'index': i,
                    'available': True,
                    'resolution': f"{width}x{height}",
                    'fps': fps,
                    'backend': cap.getBackendName()
                })
                cap.release()
            else:
                # Camera index exists but not available
                if i == 0:  # Always check index 0
                    cameras.append({
                        'index': i,
                        'available': False,
                        'resolution': 'N/A',
                        'fps': 0,
                        'backend': 'N/A'
                    })
                    
        return cameras
    
    def get_camera_properties(self, camera_index: int = 0) -> Dict:
        """Get detailed properties of a specific camera."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            return {'error': 'Camera not accessible'}
        
        properties = {
            'index': camera_index,
            'backend': cap.getBackendName(),
            'frame_width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'frame_height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
            'format': cap.get(cv2.CAP_PROP_FORMAT),
            'mode': cap.get(cv2.CAP_PROP_MODE),
            'brightness': cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': cap.get(cv2.CAP_PROP_SATURATION),
            'exposure': cap.get(cv2.CAP_PROP_EXPOSURE),
            'auto_exposure': cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
            'buffersize': cap.get(cv2.CAP_PROP_BUFFERSIZE)
        }
        
        # Test frame capture
        ret, frame = cap.read()
        properties['can_capture'] = ret
        
        if ret and frame is not None:
            properties['actual_resolution'] = f"{frame.shape[1]}x{frame.shape[0]}"
            properties['color_channels'] = frame.shape[2] if len(frame.shape) > 2 else 1
            
        cap.release()
        return properties
    
    def test_camera_performance(self, camera_index: int = 0, duration: int = 5) -> Dict:
        """Test camera performance over a period of time."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            return {'error': 'Camera not accessible'}
        
        # Set optimal properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"Testing camera performance for {duration} seconds...")
        
        frames_captured = 0
        frames_failed = 0
        frame_times = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            frame_start = time.time()
            ret, frame = cap.read()
            frame_time = time.time() - frame_start
            
            if ret:
                frames_captured += 1
                frame_times.append(frame_time)
            else:
                frames_failed += 1
        
        elapsed = time.time() - start_time
        
        # Calculate metrics
        avg_fps = frames_captured / elapsed if elapsed > 0 else 0
        avg_frame_time = np.mean(frame_times) if frame_times else 0
        max_frame_time = np.max(frame_times) if frame_times else 0
        min_frame_time = np.min(frame_times) if frame_times else 0
        
        performance = {
            'duration': elapsed,
            'frames_captured': frames_captured,
            'frames_failed': frames_failed,
            'average_fps': round(avg_fps, 2),
            'average_frame_time_ms': round(avg_frame_time * 1000, 2),
            'max_frame_time_ms': round(max_frame_time * 1000, 2),
            'min_frame_time_ms': round(min_frame_time * 1000, 2),
            'capture_success_rate': round((frames_captured / (frames_captured + frames_failed)) * 100, 2) if frames_captured + frames_failed > 0 else 0
        }
        
        cap.release()
        return performance
    
    def check_camera_health(self, camera_index: int = 0) -> Dict:
        """Perform comprehensive camera health check."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'camera_index': camera_index,
            'status': 'unknown',
            'issues': [],
            'recommendations': []
        }
        
        # Check if camera can be opened
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            health_status['status'] = 'error'
            health_status['issues'].append('Camera cannot be opened')
            health_status['recommendations'].append('Check if camera is connected')
            health_status['recommendations'].append('Check camera permissions')
            health_status['recommendations'].append('Try closing other applications using the camera')
            return health_status
        
        # Check frame capture
        ret, frame = cap.read()
        if not ret:
            health_status['status'] = 'error'
            health_status['issues'].append('Cannot capture frames')
            health_status['recommendations'].append('Check camera drivers')
            cap.release()
            return health_status
        
        # Check frame quality
        if frame is not None:
            # Check if frame is black
            if np.mean(frame) < 5:
                health_status['issues'].append('Camera producing black frames')
                health_status['recommendations'].append('Check camera lens cover')
                health_status['recommendations'].append('Check lighting conditions')
            
            # Check frame dimensions
            height, width = frame.shape[:2]
            if width < 320 or height < 240:
                health_status['issues'].append(f'Low resolution: {width}x{height}')
                health_status['recommendations'].append('Increase camera resolution settings')
        
        # Check FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps < 15:
            health_status['issues'].append(f'Low FPS: {fps}')
            health_status['recommendations'].append('Check system resources')
            health_status['recommendations'].append('Close other applications')
        
        # Overall status
        if len(health_status['issues']) == 0:
            health_status['status'] = 'healthy'
        elif len(health_status['issues']) < 2:
            health_status['status'] = 'warning'
        else:
            health_status['status'] = 'critical'
        
        cap.release()
        return health_status
    
    def monitor_continuously(self, camera_index: int = 0, interval: int = 5):
        """Monitor camera health continuously."""
        print("🎥 Starting Continuous Webcam Health Monitoring")
        print("=" * 60)
        print(f"Monitoring camera {camera_index} every {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Perform health check
                health = self.check_camera_health(camera_index)
                self.health_history.append(health)
                
                # Display status
                status_symbol = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {status_symbol} Camera Status: {health['status'].upper()}")
                
                if health['issues']:
                    print("Issues found:")
                    for issue in health['issues']:
                        print(f"  - {issue}")
                
                if health['recommendations']:
                    print("Recommendations:")
                    for rec in health['recommendations']:
                        print(f"  - {rec}")
                
                # Quick performance check
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        resolution = f"{frame.shape[1]}x{frame.shape[0]}"
                        print(f"\nCurrent: {resolution} @ {fps}fps")
                    cap.release()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.print_summary()
    
    def print_summary(self):
        """Print monitoring summary."""
        if not self.health_history:
            return
        
        print("\n📊 MONITORING SUMMARY")
        print("=" * 60)
        
        total_checks = len(self.health_history)
        healthy_checks = sum(1 for h in self.health_history if h['status'] == 'healthy')
        warning_checks = sum(1 for h in self.health_history if h['status'] == 'warning')
        error_checks = sum(1 for h in self.health_history if h['status'] == 'error')
        
        print(f"Total checks: {total_checks}")
        print(f"Healthy: {healthy_checks} ({healthy_checks/total_checks*100:.1f}%)")
        print(f"Warnings: {warning_checks} ({warning_checks/total_checks*100:.1f}%)")
        print(f"Errors: {error_checks} ({error_checks/total_checks*100:.1f}%)")
        
        # Common issues
        all_issues = []
        for h in self.health_history:
            all_issues.extend(h['issues'])
        
        if all_issues:
            print("\nMost common issues:")
            from collections import Counter
            issue_counts = Counter(all_issues)
            for issue, count in issue_counts.most_common(3):
                print(f"  - {issue}: {count} times")
    
    def get_system_info(self) -> Dict:
        """Get system and OpenCV information."""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'opencv_version': cv2.__version__,
            'opencv_build_info': cv2.getBuildInformation().split('\n')[:10],  # First 10 lines
            'python_version': platform.python_version()
        }


def main():
    """Main function to run webcam health monitoring."""
    monitor = WebcamHealthMonitor()
    
    print("🎥 WEBCAM HEALTH MONITOR")
    print("=" * 60)
    
    # System info
    print("\n1. System Information:")
    sys_info = monitor.get_system_info()
    print(f"   Platform: {sys_info['platform']}")
    print(f"   OpenCV: {sys_info['opencv_version']}")
    print(f"   Python: {sys_info['python_version']}")
    
    # Enumerate cameras
    print("\n2. Available Cameras:")
    cameras = monitor.enumerate_cameras()
    
    if not cameras:
        print("   ❌ No cameras detected!")
        return
    
    for cam in cameras:
        status = "✅" if cam['available'] else "❌"
        print(f"   {status} Camera {cam['index']}: {cam['resolution']} @ {cam['fps']}fps ({cam['backend']})")
    
    # Select available camera
    available_cameras = [c for c in cameras if c['available']]
    if not available_cameras:
        print("\n❌ No available cameras found!")
        return
    
    camera_index = available_cameras[0]['index']
    
    # Detailed properties
    print(f"\n3. Camera {camera_index} Properties:")
    properties = monitor.get_camera_properties(camera_index)
    
    if 'error' not in properties:
        print(f"   Resolution: {properties['frame_width']}x{properties['frame_height']}")
        print(f"   FPS: {properties['fps']}")
        print(f"   Backend: {properties['backend']}")
        print(f"   Can capture: {properties['can_capture']}")
        print(f"   Brightness: {properties['brightness']}")
        print(f"   Exposure: {properties['exposure']}")
    
    # Performance test
    print(f"\n4. Performance Test (5 seconds):")
    performance = monitor.test_camera_performance(camera_index, 5)
    
    if 'error' not in performance:
        print(f"   Frames captured: {performance['frames_captured']}")
        print(f"   Average FPS: {performance['average_fps']}")
        print(f"   Capture success rate: {performance['capture_success_rate']}%")
        print(f"   Avg frame time: {performance['average_frame_time_ms']}ms")
    
    # Health check
    print(f"\n5. Health Check:")
    health = monitor.check_camera_health(camera_index)
    
    status_symbol = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
    print(f"   {status_symbol} Overall status: {health['status'].upper()}")
    
    if health['issues']:
        print("   Issues:")
        for issue in health['issues']:
            print(f"     - {issue}")
    
    if health['recommendations']:
        print("   Recommendations:")
        for rec in health['recommendations']:
            print(f"     - {rec}")
    
    # Ask about continuous monitoring
    print("\n" + "=" * 60)
    print("\n6. Would you like to start continuous monitoring?")
    print("   This will check camera health every 5 seconds")
    print("   Press Enter to start or Ctrl+C to exit")
    
    try:
        input()
        monitor.monitor_continuously(camera_index, 5)
    except KeyboardInterrupt:
        print("\n👋 Exiting...")


if __name__ == "__main__":
    main()