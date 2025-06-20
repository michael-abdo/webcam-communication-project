#!/usr/bin/env python3
"""
Video Processor for Cognitive Overload Detection

This module handles video file reading and frame extraction using OpenCV.
Foundation component for the cognitive overload detection pipeline.

Author: Cognitive Overload Detection System
Version: 1.0
"""

import cv2
import os
import json
from typing import Generator, Tuple, Optional, Dict, Any
import numpy as np


class VideoProcessor:
    """
    Handles video file processing and frame extraction.
    
    Provides a clean interface for reading video files frame by frame,
    extracting metadata, and preparing frames for facial landmark detection.
    """
    
    def __init__(self, video_path: str):
        """
        Initialize video processor with a video file.
        
        Args:
            video_path (str): Path to the video file
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video file cannot be opened
        """
        self.video_path = video_path
        self.cap = None
        self.metadata = {}
        
        # Validate video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Initialize video capture
        self._initialize_capture()
        
    def _initialize_capture(self) -> None:
        """Initialize OpenCV video capture and extract metadata."""
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.video_path}")
        
        # Extract video metadata
        self.metadata = {
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration_seconds': 0,  # Will calculate after frame count
            'codec': int(self.cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        # Calculate duration
        if self.metadata['fps'] > 0:
            self.metadata['duration_seconds'] = self.metadata['frame_count'] / self.metadata['fps']
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get video metadata.
        
        Returns:
            Dict containing video metadata (fps, frame_count, width, height, etc.)
        """
        return self.metadata.copy()
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the next frame from the video.
        
        Returns:
            Tuple of (success: bool, frame: np.ndarray or None)
        """
        if self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame if ret else None
    
    def frame_generator(self) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Generator that yields frame number and frame data.
        
        Yields:
            Tuple of (frame_number: int, frame: np.ndarray)
        """
        frame_number = 0
        
        while True:
            ret, frame = self.read_frame()
            if not ret:
                break
                
            yield frame_number, frame
            frame_number += 1
    
    def extract_frames(self, output_dir: str = None, frame_interval: int = 1) -> list:
        """
        Extract frames from video and optionally save to disk.
        
        Args:
            output_dir (str, optional): Directory to save frame images
            frame_interval (int): Extract every Nth frame (1 = all frames)
            
        Returns:
            List of extracted frames as numpy arrays
        """
        frames = []
        
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for frame_num, frame in self.frame_generator():
            # Skip frames based on interval
            if frame_num % frame_interval != 0:
                continue
                
            frames.append(frame)
            
            # Save frame if output directory specified
            if output_dir:
                frame_filename = os.path.join(output_dir, f"frame_{frame_num:06d}.jpg")
                cv2.imwrite(frame_filename, frame)
        
        return frames
    
    def seek_to_frame(self, frame_number: int) -> bool:
        """
        Seek to a specific frame number.
        
        Args:
            frame_number (int): Frame number to seek to
            
        Returns:
            bool: True if seek successful, False otherwise
        """
        if self.cap is None:
            return False
        
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """
        Seek to a specific time in the video.
        
        Args:
            time_seconds (float): Time in seconds to seek to
            
        Returns:
            bool: True if seek successful, False otherwise
        """
        if self.cap is None or self.metadata['fps'] <= 0:
            return False
        
        frame_number = int(time_seconds * self.metadata['fps'])
        return self.seek_to_frame(frame_number)
    
    def close(self) -> None:
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures resources are cleaned up."""
        self.close()


def process_video_basic_test(video_path: str) -> Dict[str, Any]:
    """
    Basic test function to validate video processing works.
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        Dict with test results and metadata
    """
    try:
        with VideoProcessor(video_path) as processor:
            metadata = processor.get_metadata()
            
            # Test reading first few frames
            frame_count = 0
            test_frames = []
            
            for frame_num, frame in processor.frame_generator():
                test_frames.append({
                    'frame_number': frame_num,
                    'shape': frame.shape,
                    'dtype': str(frame.dtype)
                })
                frame_count += 1
                
                # Only test first 5 frames for validation
                if frame_count >= 5:
                    break
            
            return {
                'success': True,
                'video_path': video_path,
                'metadata': metadata,
                'frames_tested': frame_count,
                'sample_frames': test_frames,
                'message': f"Successfully processed {frame_count} frames"
            }
            
    except Exception as e:
        return {
            'success': False,
            'video_path': video_path,
            'error': str(e),
            'message': f"Failed to process video: {e}"
        }


if __name__ == "__main__":
    """
    Test the video processor with sample videos if they exist.
    """
    # Look for test videos in the test_videos directory
    test_videos_dir = "../tests/test_videos"
    
    if os.path.exists(test_videos_dir):
        test_files = [f for f in os.listdir(test_videos_dir) 
                     if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        
        if test_files:
            print("Testing VideoProcessor with available test videos:")
            for video_file in test_files:
                video_path = os.path.join(test_videos_dir, video_file)
                print(f"\n--- Testing: {video_file} ---")
                result = process_video_basic_test(video_path)
                
                if result['success']:
                    print(f"✅ {result['message']}")
                    print(f"   Metadata: {result['metadata']}")
                else:
                    print(f"❌ {result['message']}")
        else:
            print("No test videos found in test_videos directory")
    else:
        print("Test videos directory not found. VideoProcessor created successfully.")
        print("To test, add video files to: cognitive_overload/tests/test_videos/")
    
    print("\nVideoProcessor module ready for use!")