#!/usr/bin/env python3
"""
Download Sample Dataset for Validation

This script helps download and prepare sample webcam videos for validation.
It provides options for using existing videos or downloading sample datasets.
"""

import os
import json
import urllib.request
import zipfile
import shutil
from typing import List, Dict

class DatasetPreparer:
    """
    Prepares webcam video datasets for validation.
    """
    
    def __init__(self, base_dir: str = "./webcam_datasets"):
        """
        Initialize dataset preparer.
        
        Args:
            base_dir (str): Base directory for datasets
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def prepare_sample_dataset(self) -> str:
        """
        Prepare a sample dataset using existing test videos.
        
        Returns:
            str: Path to prepared dataset
        """
        sample_dir = os.path.join(self.base_dir, "sample_dataset")
        os.makedirs(sample_dir, exist_ok=True)
        
        print("=== PREPARING SAMPLE DATASET ===")
        
        # Create dataset info
        dataset_info = {
            "name": "Webcam Sample Dataset",
            "description": "Sample videos for validating face detection and cognitive metrics",
            "sources": [],
            "preparation_notes": []
        }
        
        # Check for existing videos in the project
        existing_videos = [
            "../tests/test_videos/realistic_synthetic_face.mp4"
        ]
        
        copied_count = 0
        for video_path in existing_videos:
            if os.path.exists(video_path):
                dest_path = os.path.join(sample_dir, os.path.basename(video_path))
                shutil.copy2(video_path, dest_path)
                dataset_info["sources"].append({
                    "file": os.path.basename(video_path),
                    "type": "synthetic",
                    "description": "Synthetic face video from testing"
                })
                copied_count += 1
                print(f"✅ Copied: {os.path.basename(video_path)}")
        
        # Save dataset info
        info_path = os.path.join(sample_dir, "dataset_info.json")
        with open(info_path, 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print(f"\n📁 Sample dataset prepared at: {sample_dir}")
        print(f"   Videos included: {copied_count}")
        
        # Provide instructions for real videos
        self._print_real_video_instructions(sample_dir)
        
        return sample_dir
    
    def _print_real_video_instructions(self, dataset_dir: str):
        """
        Print instructions for adding real webcam videos.
        
        Args:
            dataset_dir (str): Dataset directory path
        """
        instructions = f"""
=== ADDING REAL WEBCAM VIDEOS ===

To properly validate the system, add real webcam videos to:
{dataset_dir}

OPTION 1: Use Your Own Videos
-----------------------------
1. Record 5-10 webcam videos (30-60 seconds each)
2. Include varied conditions:
   - Different lighting (bright, dim, natural)
   - Different people
   - Natural movements and expressions
   - Some cognitive load scenarios (reading, problem-solving)
3. Save as MP4 or AVI format
4. Copy to: {dataset_dir}

OPTION 2: Public Datasets
------------------------
Consider these sources:
- YouTube Faces Database (requires registration)
- CelebA Dataset (celebrity faces)
- Your own webcam recordings

OPTION 3: Quick Test Videos
--------------------------
Record quick test videos:
1. Normal conversation (baseline)
2. Reading complex text (mild load)
3. Mental math problems (high load)
4. Relaxed state (low load)

IMPORTANT: Real human faces are essential for proper validation!
The synthetic video is only for initial testing.
"""
        print(instructions)
    
    def create_sample_videos_script(self) -> str:
        """
        Create a script to help users record sample videos.
        
        Returns:
            str: Path to the created script
        """
        script_path = os.path.join(self.base_dir, "record_sample_videos.py")
        
        script_content = '''#!/usr/bin/env python3
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
    
    print(f"\\n📹 Recording: {scenario}")
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
        
        print(f"\\n{'='*50}")
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
        
        input("\\nPress Enter when ready to start recording...")
        
        record_video(output_path, duration, scenario)
    
    print(f"\\n✅ All recordings complete! Videos saved to: {output_dir}")
    print("Copy these videos to your validation dataset directory.")

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        print(f"\n📝 Recording script created: {script_path}")
        
        return script_path

def main():
    """Prepare dataset for validation."""
    preparer = DatasetPreparer()
    
    # Prepare sample dataset
    dataset_path = preparer.prepare_sample_dataset()
    
    # Create recording script
    script_path = preparer.create_sample_videos_script()
    
    print("\n=== NEXT STEPS ===")
    print("1. Add real webcam videos to the dataset directory")
    print("2. Or use the recording script to create sample videos:")
    print(f"   python3 {script_path}")
    print("3. Then run validation:")
    print(f"   python3 dataset_validator.py {dataset_path}")

if __name__ == "__main__":
    main()