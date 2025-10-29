#!/usr/bin/env python3
"""
Core Pipeline with Foundation Enforcement

This is the MAIN pipeline module that enforces foundation-first validation
for all camera and analysis operations in the system.
"""

import sys
import os
import cv2
import time
import threading
import numpy as np
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# Add paths
sys.path.append('./camera_tools')
sys.path.append('./cognitive_overload/processing')

# Import foundation enforcer
from foundation_enforcer import requires, validator, with_foundation, FoundationValidator

# Import camera tools
from tests.quick_camera_test import test_camera
from health_monitoring.webcam_health_monitor import WebcamHealthMonitor
from dashboards.camera_status_dashboard import camera_state as dashboard_state

# Import analysis components
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
from alert_system import AlertSystem


class CorePipeline:
    """
    Core system pipeline with enforced foundation requirements.
    
    This is the CENTRAL class that all components should use.
    It ensures proper validation hierarchy is maintained.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure single pipeline instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize core pipeline with foundation enforcement."""
        if self._initialized:
            return
        
        # Core components
        self.validator = validator
        self.camera = None
        self.health_monitor = None
        self.processor = None
        self.mapper = None
        self.fatigue_detector = None
        self.alert_system = None
        
        # State tracking
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.monitoring = False
        self.streaming = False
        self.analyzing = False
        
        # Threads
        self.monitor_thread = None
        self.stream_thread = None
        self.analysis_thread = None
        
        # Metrics
        self.metrics = {
            'camera': {},
            'health': {},
            'streaming': {},
            'analysis': {}
        }
        
        # Register custom validators
        self._register_validators()
        
        self._initialized = True
        
        print("🏗️ Core Pipeline initialized with foundation enforcement")
    
    def _register_validators(self):
        """Register validation functions for each layer."""
        
        # Health validator
        def validate_health():
            try:
                if not self.camera or not self.camera.isOpened():
                    return {'success': False, 'details': {'error': 'Camera not initialized'}}
                
                # Check camera health
                monitor = WebcamHealthMonitor()
                health = monitor.check_camera_health(0)
                
                if health['is_accessible']:
                    return {
                        'success': True,
                        'details': {
                            'resolution': health.get('resolution'),
                            'fps': health.get('fps'),
                            'brightness': health.get('mean_brightness')
                        }
                    }
                else:
                    return {'success': False, 'details': health}
                    
            except Exception as e:
                return {'success': False, 'details': {'error': str(e)}}
        
        # Streaming validator
        def validate_streaming():
            try:
                if not self.monitoring:
                    return {'success': False, 'details': {'error': 'Monitoring not active'}}
                
                # Check if we're getting frames
                with self.frame_lock:
                    has_frame = self.current_frame is not None
                
                if has_frame:
                    return {
                        'success': True,
                        'details': {
                            'frame_rate': self.metrics['health'].get('fps', 0),
                            'frame_count': self.metrics['health'].get('frame_count', 0)
                        }
                    }
                else:
                    return {'success': False, 'details': {'error': 'No frames available'}}
                    
            except Exception as e:
                return {'success': False, 'details': {'error': str(e)}}
        
        # Analysis validator  
        def validate_analysis():
            try:
                # Check if analysis components are ready
                if not all([self.processor, self.mapper, self.fatigue_detector]):
                    return {'success': False, 'details': {'error': 'Analysis components not initialized'}}
                
                # Test with a frame
                with self.frame_lock:
                    if self.current_frame is None:
                        return {'success': False, 'details': {'error': 'No frame to analyze'}}
                    
                    # Try processing
                    test_frame = self.current_frame.copy()
                
                results = self.processor.process_static(test_frame)
                if results and results.multi_face_landmarks:
                    return {
                        'success': True,
                        'details': {
                            'face_detected': True,
                            'components_ready': True
                        }
                    }
                else:
                    return {
                        'success': True,  # Components work, just no face
                        'details': {
                            'face_detected': False,
                            'components_ready': True
                        }
                    }
                    
            except Exception as e:
                return {'success': False, 'details': {'error': str(e)}}
        
        # Register all validators
        self.validator.register_validator('health', validate_health)
        self.validator.register_validator('streaming', validate_streaming)
        self.validator.register_validator('analysis', validate_analysis)
    
    # FOUNDATION LAYER
    # ================
    
    @requires('foundation')
    def initialize_camera(self, camera_index: int = 0) -> bool:
        """
        Initialize camera hardware.
        REQUIRES: Foundation validation passed.
        """
        print(f"🎥 Initializing camera {camera_index}...")
        
        if self.camera and self.camera.isOpened():
            print("⚠️  Camera already initialized")
            return True
        
        try:
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Failed to open camera {camera_index}")
            
            # Configure camera
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.metrics['camera'] = {
                'index': camera_index,
                'resolution': f"{actual_width}x{actual_height}",
                'fps': actual_fps,
                'initialized_at': datetime.now().isoformat()
            }
            
            print(f"✅ Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.validator.invalidate_layer('foundation', cascade=True)
            raise
    
    # HEALTH LAYER
    # ============
    
    @requires('foundation', 'health')
    def start_health_monitoring(self) -> bool:
        """
        Start health monitoring thread.
        REQUIRES: Foundation + Health validation passed.
        """
        print("📊 Starting health monitoring...")
        
        if self.monitoring:
            print("⚠️  Health monitoring already active")
            return True
        
        # Ensure camera is initialized
        if not self.camera:
            self.initialize_camera()
        
        # Create health monitor
        self.health_monitor = WebcamHealthMonitor()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Wait for first frame
        time.sleep(0.5)
        
        print("✅ Health monitoring active")
        return True
    
    def _monitor_loop(self):
        """Background thread for health monitoring."""
        frame_count = 0
        frame_times = []
        brightness_history = []
        
        while self.monitoring:
            try:
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
                        
                        brightness = np.mean(frame)
                        brightness_history.append(brightness)
                        if len(brightness_history) > 30:
                            brightness_history.pop(0)
                        
                        frame_count += 1
                        
                        # Update metrics
                        self.metrics['health'] = {
                            'fps': round(1 / np.mean(frame_times), 1) if frame_times else 0,
                            'brightness': round(brightness, 2),
                            'avg_brightness': round(np.mean(brightness_history), 2),
                            'frame_count': frame_count,
                            'frame_time_ms': round(frame_time * 1000, 2),
                            'health_status': self._determine_health_status(brightness, frame_times)
                        }
                    else:
                        # Frame capture failed
                        self.metrics['health']['capture_failures'] = \
                            self.metrics['health'].get('capture_failures', 0) + 1
                
            except Exception as e:
                print(f"❌ Monitor loop error: {e}")
                self.metrics['health']['last_error'] = str(e)
            
            time.sleep(0.033)  # ~30 FPS
    
    def _determine_health_status(self, brightness: float, frame_times: list) -> str:
        """Determine overall health status."""
        if not frame_times:
            return 'unknown'
        
        avg_fps = 1 / np.mean(frame_times) if frame_times else 0
        
        if avg_fps < 15:
            return 'poor'
        elif brightness < 10:
            return 'dark'
        elif brightness > 240:
            return 'overexposed'
        elif avg_fps < 25:
            return 'slow'
        else:
            return 'healthy'
    
    # STREAMING LAYER
    # ===============
    
    @requires('foundation', 'health', 'streaming')
    def start_video_streaming(self) -> bool:
        """
        Start video streaming.
        REQUIRES: Foundation + Health + Streaming validation passed.
        """
        print("📹 Starting video streaming...")
        
        if self.streaming:
            print("⚠️  Video streaming already active")
            return True
        
        # Ensure monitoring is active
        if not self.monitoring:
            self.start_health_monitoring()
        
        # Start streaming thread
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        print("✅ Video streaming active")
        return True
    
    def _stream_loop(self):
        """Background thread for video streaming."""
        stream_count = 0
        
        while self.streaming:
            try:
                with self.frame_lock:
                    if self.current_frame is not None:
                        # In real implementation, encode and stream frame
                        stream_count += 1
                        
                        self.metrics['streaming'] = {
                            'frames_streamed': stream_count,
                            'streaming_fps': self.metrics['health'].get('fps', 0),
                            'last_frame_time': datetime.now().isoformat()
                        }
                
            except Exception as e:
                print(f"❌ Stream loop error: {e}")
                self.metrics['streaming']['last_error'] = str(e)
            
            time.sleep(0.033)  # Match capture rate
    
    @requires('foundation', 'health', 'streaming')
    def get_frame(self, annotated: bool = False) -> Optional[np.ndarray]:
        """
        Get current frame.
        REQUIRES: Full streaming stack validated.
        """
        with self.frame_lock:
            if self.current_frame is None:
                return None
            
            frame = self.current_frame.copy()
        
        if annotated:
            # Add annotations
            self._annotate_frame(frame)
        
        return frame
    
    def _annotate_frame(self, frame: np.ndarray):
        """Add status annotations to frame."""
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add metrics
        if self.metrics['health']:
            fps = self.metrics['health'].get('fps', 0)
            cv2.putText(frame, f"FPS: {fps}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            brightness = self.metrics['health'].get('brightness', 0)
            cv2.putText(frame, f"Brightness: {brightness:.1f}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add validation status
        status_y = 120
        for layer in ['foundation', 'health', 'streaming', 'analysis']:
            status = self.validator.get_status(layer)
            color = (0, 255, 0) if status['valid'] else (0, 0, 255)
            cv2.putText(frame, f"{layer}: {status['status']}", (10, status_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            status_y += 25
    
    # ANALYSIS LAYER
    # ==============
    
    @requires('foundation', 'health', 'streaming', 'analysis')
    def start_fatigue_analysis(self) -> bool:
        """
        Start fatigue analysis.
        REQUIRES: ALL layers validated.
        """
        print("🧠 Starting fatigue analysis...")
        
        if self.analyzing:
            print("⚠️  Fatigue analysis already active")
            return True
        
        # Initialize analysis components
        try:
            self.processor = LandmarkProcessor()
            self.mapper = CognitiveLandmarkMapper()
            self.fatigue_detector = FatigueDetector()
            self.fatigue_detector.set_calibration('real')
            self.alert_system = AlertSystem()
            
            print("✅ Analysis components initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize analysis components: {e}")
            raise
        
        # Ensure streaming is active
        if not self.streaming:
            self.start_video_streaming()
        
        # Start analysis thread
        self.analyzing = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        print("✅ Fatigue analysis active")
        return True
    
    def _analysis_loop(self):
        """Background thread for fatigue analysis."""
        analysis_count = 0
        
        while self.analyzing:
            try:
                # Get current frame
                with self.frame_lock:
                    if self.current_frame is None:
                        continue
                    frame = self.current_frame.copy()
                
                # Process frame
                results = self.processor.process_static(frame)
                
                if results and results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        # Calculate eye openness
                        left_eye = self.mapper.calculate_eye_openness(face_landmarks, 'left')
                        right_eye = self.mapper.calculate_eye_openness(face_landmarks, 'right')
                        avg_openness = (left_eye + right_eye) / 2
                        
                        # Update fatigue metrics
                        fatigue_metrics = self.fatigue_detector.update(avg_openness, time.time())
                        
                        # Update alert system
                        alerts = self.alert_system.update(
                            perclos_percentage=fatigue_metrics['perclos_percentage'],
                            fatigue_level=fatigue_metrics['fatigue_level'],
                            blink_count=fatigue_metrics['blink_rate'],
                            microsleep_count=fatigue_metrics['microsleep_count']
                        )
                        
                        analysis_count += 1
                        
                        # Update metrics
                        self.metrics['analysis'] = {
                            'perclos': fatigue_metrics['perclos_percentage'],
                            'fatigue_level': fatigue_metrics['fatigue_level'],
                            'eye_openness': avg_openness,
                            'blink_rate': fatigue_metrics['blink_rate'],
                            'alert_level': alerts['alert_level'],
                            'analysis_count': analysis_count,
                            'last_analysis': datetime.now().isoformat()
                        }
                
            except Exception as e:
                print(f"❌ Analysis loop error: {e}")
                self.metrics['analysis']['last_error'] = str(e)
            
            time.sleep(0.1)  # 10 FPS for analysis
    
    @requires('foundation', 'health', 'streaming', 'analysis')
    def get_fatigue_metrics(self) -> Dict[str, Any]:
        """
        Get current fatigue metrics.
        REQUIRES: Full stack including analysis.
        """
        return self.metrics['analysis'].copy()
    
    # UTILITY METHODS
    # ===============
    
    def get_metrics(self, layer: str = None) -> Dict[str, Any]:
        """Get metrics for specific layer or all layers."""
        if layer:
            return self.metrics.get(layer, {}).copy()
        return self.metrics.copy()
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status of all layers."""
        return self.validator.get_all_status()
    
    def validate_stack(self, up_to_layer: str = 'analysis') -> bool:
        """
        Validate stack up to specified layer.
        Useful for startup sequences.
        """
        layers = ['foundation', 'health', 'streaming', 'analysis']
        
        try:
            target_index = layers.index(up_to_layer)
        except ValueError:
            print(f"❌ Unknown layer: {up_to_layer}")
            return False
        
        for i in range(target_index + 1):
            layer = layers[i]
            print(f"\n🔍 Validating {layer}...")
            
            if not self.validator.validate_layer(layer):
                print(f"❌ Validation failed at {layer}")
                return False
        
        print(f"\n✅ Stack validated up to {up_to_layer}")
        return True
    
    def shutdown(self):
        """Shutdown entire pipeline gracefully."""
        print("\n🛑 Shutting down core pipeline...")
        
        # Stop threads in reverse order
        self.analyzing = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=1)
        
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1)
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Invalidate all validations
        self.validator.invalidate_layer('foundation', cascade=True)
        
        # Clear metrics
        self.metrics = {
            'camera': {},
            'health': {},
            'streaming': {},
            'analysis': {}
        }
        
        print("✅ Core pipeline shutdown complete")
    
    def status_report(self):
        """Display comprehensive status report."""
        print("\n" + "=" * 60)
        print("📊 CORE PIPELINE STATUS REPORT")
        print("=" * 60)
        
        # Validation status
        print("\n🔍 Validation Status:")
        all_status = self.validator.get_all_status()
        
        for layer, status in all_status.items():
            icon = "✅" if status['valid'] else "❌"
            print(f"  {icon} {layer.upper()}: {status['status']}")
            
            if status.get('expires_in'):
                print(f"     Expires in: {status['expires_in']}s")
            
            if status.get('details') and status['valid']:
                print(f"     Details: {status['details']}")
        
        # Component status
        print("\n🔧 Components:")
        print(f"  Camera: {'Active' if self.camera and self.camera.isOpened() else 'Inactive'}")
        print(f"  Monitoring: {'Running' if self.monitoring else 'Stopped'}")
        print(f"  Streaming: {'Running' if self.streaming else 'Stopped'}")
        print(f"  Analysis: {'Running' if self.analyzing else 'Stopped'}")
        
        # Metrics summary
        print("\n📈 Metrics Summary:")
        
        if self.metrics['health']:
            print(f"  Health: FPS={self.metrics['health'].get('fps', 0)}, "
                  f"Brightness={self.metrics['health'].get('brightness', 0)}")
        
        if self.metrics['streaming']:
            print(f"  Streaming: Frames={self.metrics['streaming'].get('frames_streamed', 0)}")
        
        if self.metrics['analysis']:
            print(f"  Analysis: PERCLOS={self.metrics['analysis'].get('perclos', 0):.1f}%, "
                  f"Alert={self.metrics['analysis'].get('alert_level', 'none')}")
        
        print("=" * 60)


# Global pipeline instance
pipeline = CorePipeline()


# Convenience functions for easy access
def get_pipeline() -> CorePipeline:
    """Get the global pipeline instance."""
    return pipeline


def quick_start(validate_only: bool = False) -> bool:
    """
    Quick start the entire pipeline.
    
    Args:
        validate_only: If True, only validate without starting components
        
    Returns:
        bool: True if successful
    """
    p = get_pipeline()
    
    try:
        # Validate entire stack
        if not p.validate_stack('analysis'):
            return False
        
        if validate_only:
            print("\n✅ Validation complete - system ready")
            return True
        
        # Start all components
        p.initialize_camera()
        p.start_health_monitoring()
        p.start_video_streaming()
        p.start_fatigue_analysis()
        
        print("\n✅ Core pipeline fully operational!")
        return True
        
    except Exception as e:
        print(f"\n❌ Quick start failed: {e}")
        return False


if __name__ == '__main__':
    print("🏗️ CORE PIPELINE TEST")
    print("=" * 60)
    
    # Test the pipeline
    if quick_start(validate_only=True):
        pipeline.status_report()
    else:
        print("\n❌ Pipeline validation failed")
        print("Please ensure camera is connected and try again")