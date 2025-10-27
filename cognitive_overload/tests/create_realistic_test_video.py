#!/usr/bin/env python3
"""
Create Realistic Test Video for MediaPipe Face Detection Validation

This script creates a sophisticated synthetic face video that closely mimics
human facial features to test if MediaPipe Face Mesh can detect it.

Also provides instructions for obtaining real human face videos.
"""

import cv2
import numpy as np
import os
import math

def create_realistic_face_frame(frame_num, total_frames, width=640, height=480):
    """
    Create a realistic face-like pattern that MediaPipe might detect.
    
    Args:
        frame_num (int): Current frame number
        total_frames (int): Total frames in video
        width (int): Frame width
        height (int): Frame height
    
    Returns:
        np.ndarray: Frame with realistic face pattern
    """
    # Create base frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add realistic skin tone background
    skin_tone = (180, 170, 150)  # Realistic skin color in BGR
    frame[:, :] = skin_tone
    
    # Face center and dimensions
    center_x, center_y = width // 2, height // 2
    face_width, face_height = 200, 250
    
    # Create face oval with gradient shading
    face_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.ellipse(face_mask, (center_x, center_y), (face_width//2, face_height//2), 0, 0, 360, 255, -1)
    
    # Apply face region with slightly different tone
    face_region = np.zeros_like(frame)
    face_region[:, :] = (190, 180, 160)  # Slightly lighter skin tone
    frame = np.where(face_mask[..., np.newaxis] > 0, face_region, frame)
    
    # Add face contour shading
    contour_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.ellipse(contour_mask, (center_x, center_y), (face_width//2 + 10, face_height//2 + 10), 0, 0, 360, 255, 5)
    darker_tone = (160, 150, 130)
    contour_region = np.zeros_like(frame)
    contour_region[:, :] = darker_tone
    frame = np.where(contour_mask[..., np.newaxis] > 0, contour_region, frame)
    
    # Animation parameter for slight movement
    animation_offset = int(5 * math.sin(2 * math.pi * frame_num / total_frames))
    
    # Left eye (detailed)
    left_eye_x = center_x - 40 + animation_offset
    left_eye_y = center_y - 30
    
    # Eye socket (darker region)
    cv2.ellipse(frame, (left_eye_x, left_eye_y), (25, 15), 0, 0, 360, (140, 130, 110), -1)
    
    # Eye white
    cv2.ellipse(frame, (left_eye_x, left_eye_y), (20, 12), 0, 0, 360, (245, 245, 245), -1)
    
    # Iris
    cv2.circle(frame, (left_eye_x, left_eye_y), 8, (120, 100, 80), -1)
    
    # Pupil
    cv2.circle(frame, (left_eye_x, left_eye_y), 4, (20, 20, 20), -1)
    
    # Eye highlight
    cv2.circle(frame, (left_eye_x - 2, left_eye_y - 2), 2, (255, 255, 255), -1)
    
    # Eyelashes/eyelids
    cv2.ellipse(frame, (left_eye_x, left_eye_y - 5), (22, 5), 0, 0, 180, (100, 90, 70), 2)
    cv2.ellipse(frame, (left_eye_x, left_eye_y + 5), (22, 5), 0, 180, 360, (100, 90, 70), 2)
    
    # Right eye (mirror of left)
    right_eye_x = center_x + 40 + animation_offset
    right_eye_y = center_y - 30
    
    # Eye socket
    cv2.ellipse(frame, (right_eye_x, right_eye_y), (25, 15), 0, 0, 360, (140, 130, 110), -1)
    
    # Eye white
    cv2.ellipse(frame, (right_eye_x, right_eye_y), (20, 12), 0, 0, 360, (245, 245, 245), -1)
    
    # Iris
    cv2.circle(frame, (right_eye_x, right_eye_y), 8, (120, 100, 80), -1)
    
    # Pupil
    cv2.circle(frame, (right_eye_x, right_eye_y), 4, (20, 20, 20), -1)
    
    # Eye highlight
    cv2.circle(frame, (right_eye_x - 2, right_eye_y - 2), 2, (255, 255, 255), -1)
    
    # Eyelashes/eyelids
    cv2.ellipse(frame, (right_eye_x, right_eye_y - 5), (22, 5), 0, 0, 180, (100, 90, 70), 2)
    cv2.ellipse(frame, (right_eye_x, right_eye_y + 5), (22, 5), 0, 180, 360, (100, 90, 70), 2)
    
    # Eyebrows
    eyebrow_y = center_y - 55
    # Left eyebrow
    cv2.ellipse(frame, (left_eye_x, eyebrow_y), (30, 8), 0, 0, 180, (80, 60, 40), -1)
    # Right eyebrow  
    cv2.ellipse(frame, (right_eye_x, eyebrow_y), (30, 8), 0, 0, 180, (80, 60, 40), -1)
    
    # Nose
    nose_x = center_x
    nose_y = center_y + 10
    
    # Nose bridge
    cv2.line(frame, (nose_x, nose_y - 30), (nose_x, nose_y + 20), (160, 150, 130), 3)
    
    # Nostrils
    cv2.ellipse(frame, (nose_x - 8, nose_y + 15), (6, 4), 0, 0, 360, (120, 110, 90), -1)
    cv2.ellipse(frame, (nose_x + 8, nose_y + 15), (6, 4), 0, 0, 360, (120, 110, 90), -1)
    
    # Nose tip highlight
    cv2.circle(frame, (nose_x, nose_y + 10), 3, (200, 190, 170), -1)
    
    # Mouth
    mouth_x = center_x
    mouth_y = center_y + 60
    
    # Mouth shape (more realistic)
    mouth_width = 50
    mouth_height = 12
    
    # Upper lip
    cv2.ellipse(frame, (mouth_x, mouth_y - 3), (mouth_width//2, mouth_height//2), 0, 0, 180, (160, 100, 100), -1)
    
    # Lower lip  
    cv2.ellipse(frame, (mouth_x, mouth_y + 3), (mouth_width//2, mouth_height//2), 0, 180, 360, (180, 120, 120), -1)
    
    # Mouth line
    cv2.ellipse(frame, (mouth_x, mouth_y), (mouth_width//2, 2), 0, 0, 180, (120, 80, 80), 2)
    
    # Lip highlights
    cv2.ellipse(frame, (mouth_x, mouth_y - 5), (mouth_width//3, 2), 0, 0, 180, (200, 140, 140), 1)
    cv2.ellipse(frame, (mouth_x, mouth_y + 5), (mouth_width//3, 2), 0, 180, 360, (200, 140, 140), 1)
    
    # Add some facial hair/stubble texture
    for i in range(100):
        x = np.random.randint(center_x - 80, center_x + 80)
        y = np.random.randint(mouth_y + 20, center_y + 100)
        if face_mask[y, x] > 0:  # Only within face region
            cv2.circle(frame, (x, y), 1, (140, 130, 110), -1)
    
    # Add some skin texture
    for i in range(200):
        x = np.random.randint(center_x - 80, center_x + 80)
        y = np.random.randint(center_y - 100, center_y + 80)
        if face_mask[y, x] > 0:  # Only within face region
            intensity = np.random.randint(-10, 10)
            current_color = frame[y, x]
            new_color = np.clip(current_color.astype(int) + intensity, 0, 255)
            frame[y, x] = new_color.astype(np.uint8)
    
    return frame

def create_realistic_test_video(output_path, duration_seconds=30, fps=30):
    """
    Create a realistic test video with synthetic face.
    
    Args:
        output_path (str): Path to save the video
        duration_seconds (int): Video duration
        fps (int): Frames per second
    """
    print(f"Creating realistic test video: {output_path}")
    
    total_frames = duration_seconds * fps
    width, height = 640, 480
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise ValueError(f"Failed to create video writer for {output_path}")
    
    print(f"Generating {total_frames} frames...")
    
    for frame_num in range(total_frames):
        # Create realistic frame
        frame = create_realistic_face_frame(frame_num, total_frames, width, height)
        
        # Write frame
        out.write(frame)
        
        # Progress feedback
        if frame_num % 60 == 0:  # Every 2 seconds at 30fps
            progress = (frame_num / total_frames) * 100
            print(f"Progress: {progress:.1f}% ({frame_num}/{total_frames} frames)")
    
    out.release()
    print(f"✅ Realistic test video created: {output_path}")
    
    return output_path

def provide_real_video_instructions():
    """
    Provide instructions for obtaining real human face videos.
    """
    instructions = """
    
    ==========================================
    INSTRUCTIONS FOR REAL FACE VIDEO TESTING
    ==========================================
    
    For comprehensive validation, you'll need actual human face video(s).
    
    OPTION 1: Record Your Own Test Video
    ------------------------------------
    1. Use phone/webcam to record 30-second video
    2. Requirements:
       - Clear view of face (front-facing)
       - Good lighting (avoid shadows)
       - Face takes up ~1/3 of frame
       - Minimal movement (slight head movements OK)
       - Person looking at camera
    
    3. Save as MP4 format
    4. Place in: cognitive_overload/tests/test_videos/
    5. Name it: real_face_test.mp4
    
    OPTION 2: Use Sample Videos
    ---------------------------
    Download sample face videos from:
    - OpenCV sample videos
    - MediaPipe test datasets
    - Any clear face video (with permission)
    
    OPTION 3: Test With This Synthetic Video First
    --------------------------------------------
    The realistic synthetic video created by this script can test:
    - Basic pipeline functionality
    - MediaPipe configuration
    - Data processing workflow
    
    But for FINAL validation, real human faces are required.
    
    VIDEO REQUIREMENTS:
    - Format: MP4, AVI, or MOV
    - Resolution: 640x480 minimum
    - Duration: 10+ seconds
    - Clear human face visible
    - Good lighting conditions
    
    ==========================================
    """
    
    print(instructions)

if __name__ == "__main__":
    """
    Create realistic test video and provide instructions.
    """
    # Ensure test videos directory exists
    test_videos_dir = "../tests/test_videos"
    os.makedirs(test_videos_dir, exist_ok=True)
    
    # Create realistic synthetic video
    synthetic_video_path = os.path.join(test_videos_dir, "realistic_synthetic_face.mp4")
    
    try:
        create_realistic_test_video(synthetic_video_path, duration_seconds=30, fps=30)
        
        # Verify video was created
        if os.path.exists(synthetic_video_path):
            file_size = os.path.getsize(synthetic_video_path) / (1024 * 1024)  # MB
            print(f"✅ Video created successfully: {file_size:.1f} MB")
        else:
            print("❌ Failed to create video file")
            
    except Exception as e:
        print(f"❌ Error creating video: {e}")
    
    # Provide instructions for real video
    provide_real_video_instructions()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Test with synthetic video first")
    print("2. Obtain real human face video")
    print("3. Run comprehensive validation")
    print("4. Only proceed if face detection works reliably")