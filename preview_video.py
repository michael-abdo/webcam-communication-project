#!/usr/bin/env python3
"""
Preview a video file frame by frame
"""

import cv2
import sys

def preview_video(video_path):
    """Preview video with frame controls."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video: {video_path}")
    print(f"FPS: {fps:.1f}, Total frames: {frame_count}")
    print("\nControls:")
    print("  SPACE - Play/Pause")
    print("  RIGHT - Next frame")
    print("  LEFT  - Previous frame") 
    print("  ESC/Q - Quit")
    
    frame_num = 0
    paused = True
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("\nEnd of video reached")
                break
            frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break
        
        # Add frame info
        info_text = f"Frame {frame_num}/{frame_count} | {'PAUSED' if paused else 'PLAYING'}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Video Preview', frame)
        
        # Handle key presses
        if paused:
            key = cv2.waitKey(0) & 0xFF
        else:
            key = cv2.waitKey(int(1000/fps)) & 0xFF
        
        if key == ord('q') or key == 27:  # ESC
            break
        elif key == ord(' '):  # SPACE
            paused = not paused
        elif key == 83 and paused:  # RIGHT arrow
            frame_num = min(frame_num + 1, frame_count - 1)
        elif key == 81 and paused:  # LEFT arrow
            frame_num = max(frame_num - 1, 0)
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Default to one of the sample videos
    video_path = "cognitive_overload/validation/real_face_datasets/synthetic_realistic/synthetic_neutral.mp4"
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    
    preview_video(video_path)