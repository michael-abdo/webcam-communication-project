#!/usr/bin/env python3
"""
Landmark Visualization Module

This module provides functions to visualize MediaPipe Face Mesh landmarks
on video frames for validation and debugging purposes.
"""

import cv2
import numpy as np
import json
from typing import List, Tuple, Dict, Any
import os

class LandmarkVisualizer:
    """
    Visualize facial landmarks on video frames.
    """
    
    def __init__(self):
        """Initialize the visualizer with default drawing parameters."""
        self.landmark_color = (0, 255, 0)  # Green
        self.landmark_radius = 1
        self.connection_color = (255, 255, 255)  # White
        self.connection_thickness = 1
        self.text_color = (255, 255, 255)  # White
        self.text_font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_scale = 0.6
        
        # Key landmark indices for validation
        self.key_landmarks = {
            'nose_tip': 1,
            'left_eye_center': 468,
            'right_eye_center': 473,
            'mouth_center': 13,
            'chin': 175,
            'forehead': 9
        }
    
    def draw_landmarks_on_frame(self, frame: np.ndarray, landmarks: List[Dict], 
                               show_all: bool = False, show_key_only: bool = True) -> np.ndarray:
        """
        Draw landmarks on a video frame.
        
        Args:
            frame (np.ndarray): Input video frame
            landmarks (List[Dict]): List of landmark dictionaries with x, y coordinates
            show_all (bool): Whether to show all 468 landmarks
            show_key_only (bool): Whether to show only key facial feature landmarks
            
        Returns:
            np.ndarray: Frame with landmarks drawn
        """
        if not landmarks:
            return frame
            
        frame_with_landmarks = frame.copy()
        
        if show_all:
            # Draw all landmarks
            for i, landmark in enumerate(landmarks):
                x, y = landmark['x'], landmark['y']
                cv2.circle(frame_with_landmarks, (x, y), self.landmark_radius, self.landmark_color, -1)
        
        if show_key_only:
            # Draw key landmarks with labels
            for label, idx in self.key_landmarks.items():
                if idx < len(landmarks):
                    landmark = landmarks[idx]
                    x, y = landmark['x'], landmark['y']
                    
                    # Draw landmark point
                    cv2.circle(frame_with_landmarks, (x, y), 3, (0, 0, 255), -1)  # Red for key points
                    
                    # Add label
                    label_pos = (x + 5, y - 5)
                    cv2.putText(frame_with_landmarks, label, label_pos, 
                              self.text_font, self.text_scale, self.text_color, 1)
        
        # Add frame info
        info_text = f"Landmarks: {len(landmarks)}"
        cv2.putText(frame_with_landmarks, info_text, (10, 30), 
                   self.text_font, self.text_scale, self.text_color, 1)
        
        return frame_with_landmarks
    
    def create_validation_video(self, video_path: str, landmarks_json_path: str, 
                               output_path: str, max_frames: int = 30) -> bool:
        """
        Create a validation video with landmarks overlaid.
        
        Args:
            video_path (str): Path to original video
            landmarks_json_path (str): Path to landmarks JSON file
            output_path (str): Path to save validation video
            max_frames (int): Maximum frames to process
            
        Returns:
            bool: Success status
        """
        try:
            # Load landmarks data
            with open(landmarks_json_path, 'r') as f:
                landmarks_data = json.load(f)
            
            # Open original video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Failed to open video: {video_path}")
                return False
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Failed to create output video: {output_path}")
                return False
            
            print(f"Creating validation video: {output_path}")
            print(f"Processing up to {max_frames} frames...")
            
            frame_count = 0
            landmarks_idx = 0
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Get corresponding landmarks
                if landmarks_idx < len(landmarks_data['landmarks']):
                    frame_landmarks_data = landmarks_data['landmarks'][landmarks_idx]
                    landmarks = frame_landmarks_data.get('landmarks', [])
                    
                    # Draw landmarks on frame
                    frame_with_landmarks = self.draw_landmarks_on_frame(
                        frame, landmarks, show_all=True, show_key_only=True
                    )
                    
                    # Add validation info
                    validation_info = f"Frame {frame_count}: {len(landmarks)} landmarks detected"
                    cv2.putText(frame_with_landmarks, validation_info, (10, height - 20),
                              self.text_font, self.text_scale, (0, 255, 255), 1)
                    
                    out.write(frame_with_landmarks)
                    landmarks_idx += 1
                else:
                    # No landmarks for this frame
                    validation_info = f"Frame {frame_count}: No landmarks"
                    cv2.putText(frame, validation_info, (10, height - 20),
                              self.text_font, self.text_scale, (0, 0, 255), 1)
                    out.write(frame)
                
                frame_count += 1
                
                if frame_count % 10 == 0:
                    progress = (frame_count / max_frames) * 100
                    print(f"Progress: {progress:.1f}% ({frame_count}/{max_frames} frames)")
            
            cap.release()
            out.release()
            
            print(f"✅ Validation video created: {output_path}")
            print(f"   Processed {frame_count} frames")
            return True
            
        except Exception as e:
            print(f"❌ Error creating validation video: {e}")
            return False
    
    def analyze_landmark_positions(self, landmarks_json_path: str) -> Dict[str, Any]:
        """
        Analyze landmark positions for validation.
        
        Args:
            landmarks_json_path (str): Path to landmarks JSON file
            
        Returns:
            Dict with analysis results
        """
        try:
            with open(landmarks_json_path, 'r') as f:
                data = json.load(f)
            
            analysis = {
                'total_frames': len(data['landmarks']),
                'frames_with_detection': 0,
                'key_landmark_positions': {},
                'coordinate_ranges': {'x': [float('inf'), -float('inf')], 
                                    'y': [float('inf'), -float('inf')]}
            }
            
            for frame_data in data['landmarks']:
                landmarks = frame_data.get('landmarks', [])
                
                if landmarks:
                    analysis['frames_with_detection'] += 1
                    
                    # Track coordinate ranges
                    for lm in landmarks:
                        x, y = lm['x'], lm['y']
                        analysis['coordinate_ranges']['x'][0] = min(analysis['coordinate_ranges']['x'][0], x)
                        analysis['coordinate_ranges']['x'][1] = max(analysis['coordinate_ranges']['x'][1], x)
                        analysis['coordinate_ranges']['y'][0] = min(analysis['coordinate_ranges']['y'][0], y)
                        analysis['coordinate_ranges']['y'][1] = max(analysis['coordinate_ranges']['y'][1], y)
                    
                    # Analyze key landmarks
                    for label, idx in self.key_landmarks.items():
                        if idx < len(landmarks):
                            lm = landmarks[idx]
                            if label not in analysis['key_landmark_positions']:
                                analysis['key_landmark_positions'][label] = []
                            analysis['key_landmark_positions'][label].append((lm['x'], lm['y']))
            
            analysis['detection_rate'] = analysis['frames_with_detection'] / analysis['total_frames']
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing landmarks: {e}")
            return {}

def main():
    """
    Main function to create validation video and analyze landmarks.
    """
    # Paths
    video_path = "../tests/test_videos/realistic_synthetic_face.mp4"
    landmarks_path = "../data/processed_results/realistic_test_landmarks.json"
    validation_video_path = "../data/processed_results/validation_video.mp4"
    
    # Create visualizer
    visualizer = LandmarkVisualizer()
    
    # Create validation video
    print("=== CREATING LANDMARK VALIDATION VIDEO ===")
    success = visualizer.create_validation_video(
        video_path, landmarks_path, validation_video_path, max_frames=30
    )
    
    if success:
        # Analyze landmark positions
        print("\n=== ANALYZING LANDMARK POSITIONS ===")
        analysis = visualizer.analyze_landmark_positions(landmarks_path)
        
        if analysis:
            print(f"Detection rate: {analysis['detection_rate']:.1%}")
            print(f"Frames with detection: {analysis['frames_with_detection']}/{analysis['total_frames']}")
            print(f"X coordinate range: {analysis['coordinate_ranges']['x']}")
            print(f"Y coordinate range: {analysis['coordinate_ranges']['y']}")
            
            print("\nKey landmark positions (first frame):")
            for label, positions in analysis['key_landmark_positions'].items():
                if positions:
                    x, y = positions[0]
                    print(f"  {label}: ({x}, {y})")
    
    print(f"\n✅ Validation complete. Check video: {validation_video_path}")

if __name__ == "__main__":
    main()