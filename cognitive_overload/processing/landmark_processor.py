#!/usr/bin/env python3
"""
Landmark Processor for Cognitive Overload Detection

This module integrates MediaPipe Face Mesh with VideoProcessor to extract
468 facial landmarks from video frames for cognitive overload analysis.

Author: Cognitive Overload Detection System
Version: 1.0
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from video_processor import VideoProcessor


class LandmarkProcessor:
    """
    Processes video frames to extract facial landmarks using MediaPipe Face Mesh.
    
    Integrates with VideoProcessor to provide facial landmark detection
    specifically optimized for cognitive overload detection.
    """
    
    def __init__(self, video_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize landmark processor with video file and MediaPipe configuration.
        
        Args:
            video_path (str): Path to video file
            config (dict, optional): MediaPipe Face Mesh configuration
        """
        self.video_path = video_path
        self.video_processor = VideoProcessor(video_path)
        
        # Default MediaPipe Face Mesh configuration optimized for cognitive overload detection
        default_config = {
            'static_image_mode': False,          # Process video frames
            'max_num_faces': 1,                  # Single person analysis
            'refine_landmarks': True,            # Better accuracy around eyes/mouth
            'min_detection_confidence': 0.7,     # Balance accuracy vs detection
            'min_tracking_confidence': 0.5       # Consistent tracking
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(**self.config)
        
        # Drawing utilities for visualization
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Landmark data storage
        self.landmarks_data = []
        self.processing_metadata = {}
    
    def get_video_metadata(self) -> Dict[str, Any]:
        """Get video metadata from underlying VideoProcessor."""
        return self.video_processor.get_metadata()
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Process a single frame to extract facial landmarks.
        
        Args:
            frame (np.ndarray): Input video frame
            
        Returns:
            Dict containing landmark data or None if no face detected
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame with MediaPipe Face Mesh
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            # Extract first face (max_num_faces=1, so only one expected)
            face_landmarks = results.multi_face_landmarks[0]
            
            # Convert normalized landmarks to pixel coordinates
            h, w, _ = frame.shape
            landmarks = []
            
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                z = landmark.z  # Relative depth
                landmarks.append({
                    'x': x,
                    'y': y, 
                    'z': z,
                    'x_norm': landmark.x,  # Keep normalized coords too
                    'y_norm': landmark.y,
                    'z_norm': landmark.z
                })
            
            return {
                'landmarks': landmarks,
                'landmark_count': len(landmarks),
                'frame_shape': frame.shape,
                'face_detected': True
            }
        else:
            return {
                'landmarks': [],
                'landmark_count': 0,
                'frame_shape': frame.shape,
                'face_detected': False
            }
    
    def process_video(self, output_path: str = None, frame_interval: int = 1) -> Dict[str, Any]:
        """
        Process entire video to extract landmarks from all frames.
        
        Args:
            output_path (str, optional): Path to save landmark data as JSON
            frame_interval (int): Process every Nth frame (1 = all frames)
            
        Returns:
            Dict containing all processing results and metadata
        """
        print(f"Processing video: {self.video_path}")
        print(f"MediaPipe config: {self.config}")
        
        # Initialize processing
        self.landmarks_data = []
        video_metadata = self.get_video_metadata()
        frames_processed = 0
        faces_detected = 0
        
        # Process frames
        for frame_num, frame in self.video_processor.frame_generator():
            # Skip frames based on interval
            if frame_num % frame_interval != 0:
                continue
            
            # Extract landmarks from frame
            frame_data = self.process_frame(frame)
            
            if frame_data:
                frame_data['frame_number'] = frame_num
                frame_data['timestamp'] = frame_num / video_metadata['fps'] if video_metadata['fps'] > 0 else 0
                
                self.landmarks_data.append(frame_data)
                frames_processed += 1
                
                if frame_data['face_detected']:
                    faces_detected += 1
                
                # Progress feedback
                if frames_processed % 30 == 0:  # Every 30 processed frames
                    print(f"Processed {frames_processed} frames, {faces_detected} with faces detected")
        
        # Compile processing metadata
        self.processing_metadata = {
            'video_path': self.video_path,
            'video_metadata': video_metadata,
            'processing_config': self.config,
            'total_frames_processed': frames_processed,
            'frames_with_faces': faces_detected,
            'face_detection_rate': faces_detected / frames_processed if frames_processed > 0 else 0,
            'frame_interval': frame_interval,
            'landmark_count_per_face': 468  # MediaPipe Face Mesh standard
        }
        
        # Save results if output path specified
        if output_path:
            self.save_landmarks(output_path)
        
        print(f"✅ Processing complete: {frames_processed} frames, {faces_detected} faces detected")
        print(f"   Face detection rate: {self.processing_metadata['face_detection_rate']:.1%}")
        
        return {
            'landmarks_data': self.landmarks_data,
            'metadata': self.processing_metadata,
            'success': True
        }
    
    def save_landmarks(self, output_path: str) -> None:
        """
        Save landmark data to JSON file.
        
        Args:
            output_path (str): Path to save JSON file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare data for JSON serialization
        output_data = {
            'metadata': self.processing_metadata,
            'landmarks': self.landmarks_data
        }
        
        # Save to JSON file
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Landmarks saved to: {output_path}")
    
    def visualize_landmarks(self, frame: np.ndarray, landmarks_data: Dict[str, Any]) -> np.ndarray:
        """
        Draw landmarks on a frame for visualization.
        
        Args:
            frame (np.ndarray): Input frame
            landmarks_data (dict): Landmark data from process_frame()
            
        Returns:
            Frame with landmarks drawn
        """
        if not landmarks_data['face_detected']:
            return frame
        
        # Draw landmarks on frame
        annotated_frame = frame.copy()
        
        # Draw landmark points
        for landmark in landmarks_data['landmarks']:
            x, y = landmark['x'], landmark['y']
            cv2.circle(annotated_frame, (x, y), 1, (0, 255, 0), -1)
        
        # Add text overlay
        text = f"Landmarks: {landmarks_data['landmark_count']}"
        cv2.putText(annotated_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return annotated_frame
    
    def close(self) -> None:
        """Release resources."""
        if hasattr(self, 'video_processor'):
            self.video_processor.close()
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_landmark_processor_basic() -> Dict[str, Any]:
    """
    Basic test function to validate MediaPipe Face Mesh integration.
    
    Returns:
        Dict with test results
    """
    import tempfile
    
    print("Testing LandmarkProcessor with synthetic video...")
    
    # Create synthetic test video with simple face-like pattern
    temp_dir = tempfile.mkdtemp()
    test_video_path = os.path.join(temp_dir, 'test_face_video.mp4')
    
    try:
        # Create test video with face-like patterns
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(test_video_path, fourcc, 30.0, (640, 480))
        
        for i in range(10):
            # Create frame with simple face-like structure
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add face-like oval
            center_x, center_y = 320, 240
            cv2.ellipse(frame, (center_x, center_y), (80, 100), 0, 0, 360, (100, 100, 100), -1)
            
            # Add eye-like circles
            cv2.circle(frame, (center_x - 25, center_y - 20), 8, (200, 200, 200), -1)
            cv2.circle(frame, (center_x + 25, center_y - 20), 8, (200, 200, 200), -1)
            
            # Add mouth-like line
            cv2.line(frame, (center_x - 15, center_y + 30), (center_x + 15, center_y + 30), (200, 200, 200), 3)
            
            out.write(frame)
        
        out.release()
        
        # Test LandmarkProcessor
        with LandmarkProcessor(test_video_path) as processor:
            # Process just first few frames
            test_results = []
            
            for frame_num, frame in processor.video_processor.frame_generator():
                if frame_num >= 3:  # Test first 3 frames only
                    break
                
                frame_data = processor.process_frame(frame)
                test_results.append({
                    'frame_number': frame_num,
                    'face_detected': frame_data['face_detected'],
                    'landmark_count': frame_data['landmark_count']
                })
            
            return {
                'success': True,
                'message': f"LandmarkProcessor tested successfully on {len(test_results)} frames",
                'test_results': test_results,
                'mediapipe_config': processor.config
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f"LandmarkProcessor test failed: {e}",
            'error': str(e)
        }
    finally:
        # Clean up
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
        os.rmdir(temp_dir)


if __name__ == "__main__":
    """
    Test MediaPipe Face Mesh integration.
    """
    print("=== Testing MediaPipe Face Mesh Integration ===")
    
    result = test_landmark_processor_basic()
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   MediaPipe config: {result['mediapipe_config']}")
        for test in result['test_results']:
            print(f"   Frame {test['frame_number']}: Face detected={test['face_detected']}, Landmarks={test['landmark_count']}")
    else:
        print(f"❌ {result['message']}")
    
    print("\nLandmarkProcessor ready for facial landmark extraction!")