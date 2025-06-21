#!/usr/bin/env python3
"""
Example: Webcam System with Enforced Foundation Requirements

Shows how to integrate foundation enforcement into real code.
"""

import sys
import cv2
import time
import threading
import numpy as np

sys.path.append('./camera_tools')
from foundation_enforcer import requires, validator, with_foundation

# Register custom validators for each layer
def validate_health():
    """Custom health validation logic."""
    try:
        # Check if we can access camera settings
        test_cap = cv2.VideoCapture(0)
        if test_cap.isOpened():
            fps = test_cap.get(cv2.CAP_PROP_FPS)
            width = test_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = test_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            test_cap.release()
            
            return {
                'success': True,
                'details': {
                    'fps': fps,
                    'resolution': f'{int(width)}x{int(height)}'
                }
            }
    except:
        pass
    
    return {'success': False, 'details': {'error': 'Cannot check camera health'}}

def validate_streaming():
    """Custom streaming validation - check if we can capture frames."""
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                return {
                    'success': True,
                    'details': {
                        'test_frame_shape': frame.shape,
                        'test_frame_mean': np.mean(frame)
                    }
                }
    except:
        pass
    
    return {'success': False, 'details': {'error': 'Cannot capture test frame'}}

# Register validators
validator.register_validator('health', validate_health)
validator.register_validator('streaming', validate_streaming)


class EnforcedCameraSystem:
    """
    Camera system with strict foundation enforcement.
    Higher-level functions cannot run without lower validations.
    """
    
    def __init__(self):
        self.camera = None
        self.monitor_thread = None
        self.stream_thread = None
        self.monitoring = False
        self.streaming = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.metrics = {}
    
    @requires('foundation')
    def initialize_camera(self):
        """
        Initialize camera hardware.
        Can ONLY run if foundation validation passed.
        """
        print("🎥 Initializing camera...")
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera")
        
        # Configure camera
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Camera initialized successfully")
        return True
    
    @requires('foundation', 'health')
    def start_health_monitoring(self):
        """
        Start health monitoring.
        Can ONLY run if foundation AND health validation passed.
        """
        print("📊 Starting health monitoring...")
        
        if not self.camera:
            self.initialize_camera()
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("✅ Health monitoring active")
        return True
    
    @requires('foundation', 'health', 'streaming')
    def start_video_streaming(self):
        """
        Start video streaming.
        Can ONLY run if ALL lower layers validated.
        """
        print("📹 Starting video streaming...")
        
        if not self.monitoring:
            self.start_health_monitoring()
        
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        print("✅ Video streaming active")
        return True
    
    @requires('foundation', 'health', 'streaming', 'analysis')
    def start_ai_analysis(self):
        """
        Start AI analysis.
        Can ONLY run if ENTIRE stack is validated.
        """
        print("🧠 Starting AI analysis...")
        
        if not self.streaming:
            self.start_video_streaming()
        
        # In real implementation, start AI processing
        print("✅ AI analysis active")
        return True
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        frame_count = 0
        frame_times = []
        
        while self.monitoring:
            if self.camera and self.camera.isOpened():
                start_time = time.time()
                ret, frame = self.camera.read()
                
                if ret and frame is not None:
                    # Store frame for streaming
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                    
                    # Calculate metrics
                    frame_time = time.time() - start_time
                    frame_times.append(frame_time)
                    if len(frame_times) > 30:
                        frame_times.pop(0)
                    
                    frame_count += 1
                    
                    # Update metrics
                    self.metrics = {
                        'fps': round(1 / np.mean(frame_times), 1) if frame_times else 0,
                        'brightness': round(np.mean(frame), 2),
                        'frame_count': frame_count
                    }
            
            time.sleep(0.033)  # ~30 FPS
    
    def _stream_loop(self):
        """Background streaming loop."""
        while self.streaming:
            # In real implementation, stream frames to clients
            with self.frame_lock:
                if self.current_frame is not None:
                    # Process/encode frame for streaming
                    pass
            
            time.sleep(0.033)
    
    def get_current_frame(self):
        """
        Get current frame for display.
        Requires streaming to be active.
        """
        # This uses context manager pattern
        with with_foundation(['foundation', 'health', 'streaming']):
            with self.frame_lock:
                return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_metrics(self):
        """
        Get current metrics.
        Requires at least health monitoring.
        """
        # Another way to enforce requirements
        if not validator.validate_layer('health'):
            raise RuntimeError("Health monitoring not active")
        
        return self.metrics.copy()
    
    def shutdown(self):
        """Shutdown system."""
        print("\n🛑 Shutting down system...")
        
        self.streaming = False
        self.monitoring = False
        
        if self.stream_thread:
            self.stream_thread.join(timeout=1)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Invalidate all validations
        validator.invalidate_layer('foundation', cascade=True)
        
        print("✅ System shutdown complete")
    
    def status_report(self):
        """Show system status."""
        print("\n📊 CAMERA SYSTEM STATUS")
        print("=" * 50)
        
        # Show validation status
        all_status = validator.get_all_status()
        
        print("Validation Layers:")
        for layer, status in all_status.items():
            icon = "✅" if status['valid'] else "❌"
            print(f"  {icon} {layer}: {status['status']}")
            if status.get('expires_in'):
                print(f"     (expires in {status['expires_in']}s)")
        
        print("\nComponents:")
        print(f"  Camera: {'Active' if self.camera and self.camera.isOpened() else 'Inactive'}")
        print(f"  Monitoring: {'Running' if self.monitoring else 'Stopped'}")
        print(f"  Streaming: {'Running' if self.streaming else 'Stopped'}")
        
        if self.metrics:
            print("\nMetrics:")
            for key, value in self.metrics.items():
                print(f"  {key}: {value}")


def demonstrate_enforcement():
    """Demonstrate the enforcement in action."""
    system = EnforcedCameraSystem()
    
    print("🏗️ FOUNDATION ENFORCEMENT DEMONSTRATION")
    print("=" * 50)
    
    # Attempt 1: Try to start streaming without foundation
    print("\n1️⃣ Attempting to stream without foundation...")
    try:
        system.start_video_streaming()
    except RuntimeError as e:
        print(f"❌ Expected failure:\n   {e}")
    
    # Attempt 2: Try to get frame without streaming
    print("\n2️⃣ Attempting to get frame without streaming...")
    try:
        frame = system.get_current_frame()
    except RuntimeError as e:
        print(f"❌ Expected failure:\n   {e}")
    
    # Attempt 3: Proper startup sequence
    print("\n3️⃣ Starting system with proper sequence...")
    
    try:
        # Initialize camera (triggers foundation validation)
        system.initialize_camera()
        
        # Start monitoring (triggers health validation)
        system.start_health_monitoring()
        time.sleep(1)  # Let it collect some metrics
        
        # Now we can get metrics
        metrics = system.get_metrics()
        print(f"\n📊 Current metrics: {metrics}")
        
        # Start streaming (triggers streaming validation)
        system.start_video_streaming()
        time.sleep(1)
        
        # Now we can get frames
        frame = system.get_current_frame()
        if frame is not None:
            print(f"\n📹 Got frame: {frame.shape}")
        
        # Show full status
        system.status_report()
        
        # Register analysis validator
        validator.register_validator('analysis',
            lambda: {'success': True, 'details': {'models_loaded': True}}
        )
        
        # Start AI (requires everything)
        system.start_ai_analysis()
        
    except Exception as e:
        print(f"\n❌ Error during startup: {e}")
    
    finally:
        # Clean shutdown
        input("\nPress Enter to shutdown...")
        system.shutdown()
        system.status_report()


if __name__ == '__main__':
    demonstrate_enforcement()