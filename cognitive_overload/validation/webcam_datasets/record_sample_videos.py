#!/usr/bin/env python3
"""
Record Sample Webcam Videos for Validation

This script helps record webcam videos with different cognitive load scenarios.
"""

import cv2
import time
import os

def record_video(output_path: str, duration: int = 30, scenario: str = ""):
    """Record a video from webcam."""
    cap = cv2.VideoCapture(0)
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"\n📹 Recording: {scenario}")
    print(f"Duration: {duration} seconds")
    print("Press 'q' to stop early")
    
    start_time = time.time()
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Add scenario text
        cv2.putText(frame, scenario, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add timer
        elapsed = time.time() - start_time
        remaining = max(0, duration - int(elapsed))
        cv2.putText(frame, f"Time: {remaining}s", (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Write and display frame
        out.write(frame)
        cv2.imshow('Recording', frame)
        frame_count += 1
        
        # Check for quit or time limit
        if cv2.waitKey(1) & 0xFF == ord('q') or elapsed >= duration:
            break
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"✅ Recorded {frame_count} frames to {output_path}")

def main():
    """Record sample videos with different cognitive scenarios."""
    output_dir = "./sample_recordings"
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = [
        ("baseline_relaxed.mp4", 30, "Baseline - Relaxed State"),
        ("reading_simple.mp4", 30, "Reading Simple Text"),
        ("reading_complex.mp4", 30, "Reading Complex Technical Text"),
        ("mental_math_easy.mp4", 30, "Mental Math - Easy (12 + 15)"),
        ("mental_math_hard.mp4", 30, "Mental Math - Hard (47 * 23)"),
        ("problem_solving.mp4", 30, "Problem Solving Task"),
    ]
    
    print("=== WEBCAM RECORDING TOOL ===")
    print("This will record sample videos for each cognitive scenario.")
    print("Position yourself with good lighting and look at the camera.")
    
    for filename, duration, scenario in scenarios:
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n{'='*50}")
        print(f"Scenario: {scenario}")
        print("Instructions:")
        if "baseline" in filename.lower():
            print("- Relax and breathe normally")
            print("- Look at the camera naturally")
        elif "reading_simple" in filename.lower():
            print("- Read this simple text out loud:")
            print("  'The cat sat on the mat. The sun is shining.'")
        elif "reading_complex" in filename.lower():
            print("- Read this complex text out loud:")
            print("  'Quantum entanglement exhibits non-local correlations")
            print("   that violate Bell inequalities in EPR experiments.'")
        elif "mental_math_easy" in filename.lower():
            print("- Solve out loud: 12 + 15, 8 + 7, 20 - 5")
        elif "mental_math_hard" in filename.lower():
            print("- Solve out loud: 47 * 23, 156 / 12, 89 * 11")
        elif "problem_solving" in filename.lower():
            print("- Think out loud: How many windows are in your house?")
            print("- Count them mentally room by room")
        
        input("\nPress Enter when ready to start recording...")
        
        record_video(output_path, duration, scenario)
    
    print(f"\n✅ All recordings complete! Videos saved to: {output_dir}")
    print("Copy these videos to your validation dataset directory.")

if __name__ == "__main__":
    main()
