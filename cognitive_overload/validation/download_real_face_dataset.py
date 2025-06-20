#!/usr/bin/env python3
"""
Download Real Face Video Dataset

This script downloads sample videos with real human faces for validation.
We'll use publicly available sample videos that are appropriate for testing.
"""

import os
import urllib.request
import urllib.error
import zipfile
import json
import numpy as np
from typing import List, Dict, Tuple

class RealFaceDatasetDownloader:
    """
    Downloads and prepares real face video datasets.
    """
    
    def __init__(self, dataset_dir: str = "./real_face_datasets"):
        """Initialize downloader."""
        self.dataset_dir = dataset_dir
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # Sample video sources (publicly available)
        self.sample_sources = [
            {
                'name': 'sample_face_1.mp4',
                'url': 'https://www.pexels.com/video/854265/download/',
                'description': 'Person speaking to camera',
                'source': 'Pexels (Free stock videos)'
            },
            {
                'name': 'sample_face_2.mp4', 
                'url': 'https://www.pexels.com/video/3394658/download/',
                'description': 'Close-up face video',
                'source': 'Pexels (Free stock videos)'
            }
        ]
    
    def download_sample_videos(self) -> List[str]:
        """
        Download sample videos with real faces.
        
        Returns:
            List[str]: Paths to downloaded videos
        """
        print("=== DOWNLOADING REAL FACE VIDEO SAMPLES ===")
        print("Note: Using publicly available sample videos for testing")
        
        downloaded_videos = []
        
        # Try to download each sample
        for sample in self.sample_sources:
            output_path = os.path.join(self.dataset_dir, sample['name'])
            
            print(f"\nDownloading: {sample['name']}")
            print(f"Description: {sample['description']}")
            
            try:
                # Download with timeout
                urllib.request.urlretrieve(
                    sample['url'], 
                    output_path,
                    reporthook=self._download_progress
                )
                
                # Verify file exists and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    downloaded_videos.append(output_path)
                    print(f"✅ Downloaded: {output_path}")
                else:
                    print(f"❌ Download failed: {sample['name']}")
                    
            except Exception as e:
                print(f"❌ Error downloading {sample['name']}: {e}")
        
        return downloaded_videos
    
    def _download_progress(self, block_num, block_size, total_size):
        """Show download progress."""
        downloaded = block_num * block_size
        percent = min(100, (downloaded / total_size) * 100)
        print(f"Progress: {percent:.1f}%", end='\r')
    
    def create_test_dataset_from_youtube_dl(self) -> str:
        """
        Create dataset using youtube-dl compatible approach.
        Note: Requires youtube-dl or yt-dlp to be installed.
        """
        print("\n=== ALTERNATIVE: Using youtube-dl for test videos ===")
        
        output_dir = os.path.join(self.dataset_dir, "youtube_samples")
        os.makedirs(output_dir, exist_ok=True)
        
        # Sample video IDs (short, face-focused videos)
        sample_videos = [
            {
                'id': 'sample1',
                'description': 'Face detection test video',
                'duration': '10s'
            }
        ]
        
        print("\nTo download videos with faces:")
        print("1. Install yt-dlp: pip install yt-dlp")
        print("2. Run: yt-dlp -f 'best[height<=480]' -o 'face_video_%(title)s.mp4' [VIDEO_URL]")
        print("3. Place videos in:", output_dir)
        
        return output_dir
    
    def use_existing_samples(self) -> Tuple[str, List[str]]:
        """
        Use existing sample videos if available.
        
        Returns:
            Tuple[str, List[str]]: Dataset directory and list of video paths
        """
        # Check common locations for sample videos
        possible_locations = [
            "/usr/share/opencv4/samples/data/",
            "/usr/share/opencv/samples/data/",
            "/opt/opencv/samples/data/",
            "./sample_videos/",
            "../sample_videos/"
        ]
        
        found_videos = []
        
        for location in possible_locations:
            if os.path.exists(location):
                # Look for video files
                for file in os.listdir(location):
                    if file.endswith(('.mp4', '.avi', '.mov')):
                        video_path = os.path.join(location, file)
                        found_videos.append(video_path)
        
        if found_videos:
            print(f"\n✅ Found {len(found_videos)} existing sample videos")
            return os.path.dirname(found_videos[0]), found_videos
        
        return None, []
    
    def create_synthetic_face_videos(self) -> List[str]:
        """
        Create more realistic synthetic face videos for testing.
        """
        import cv2
        import numpy as np
        
        output_dir = os.path.join(self.dataset_dir, "synthetic_realistic")
        os.makedirs(output_dir, exist_ok=True)
        
        videos_created = []
        
        # Create videos with different expressions
        expressions = [
            ('neutral', 'Neutral expression'),
            ('smile', 'Smiling face'),
            ('focused', 'Concentrated expression'),
            ('tired', 'Tired expression')
        ]
        
        for expr_name, description in expressions:
            output_path = os.path.join(output_dir, f"synthetic_{expr_name}.mp4")
            
            # Create video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 30, (640, 480))
            
            print(f"\nCreating synthetic video: {expr_name}")
            
            # Generate frames with expression variations
            for frame_num in range(150):  # 5 seconds at 30fps
                frame = self._create_expressive_face(frame_num, expr_name)
                out.write(frame)
            
            out.release()
            videos_created.append(output_path)
            print(f"✅ Created: {output_path}")
        
        return videos_created
    
    def _create_expressive_face(self, frame_num: int, expression: str) -> np.ndarray:
        """Create a frame with an expressive synthetic face."""
        import numpy as np
        import cv2
        
        # Create base frame
        frame = np.full((480, 640, 3), (200, 190, 180), dtype=np.uint8)
        
        # Face parameters
        center_x, center_y = 320, 240
        
        # Add subtle movement
        offset = int(3 * np.sin(frame_num * 0.1))
        center_x += offset
        
        # Face outline
        cv2.ellipse(frame, (center_x, center_y), (100, 130), 0, 0, 360, (180, 170, 160), -1)
        
        # Eyes with expression
        eye_openness = 12
        if expression == 'tired':
            eye_openness = 8  # Smaller eyes
        elif expression == 'focused':
            eye_openness = 14  # Wider eyes
        
        # Left eye
        cv2.ellipse(frame, (center_x - 35, center_y - 30), (20, eye_openness), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (center_x - 35, center_y - 30), 8, (50, 100, 50), -1)
        cv2.circle(frame, (center_x - 35, center_y - 30), 3, (0, 0, 0), -1)
        
        # Right eye
        cv2.ellipse(frame, (center_x + 35, center_y - 30), (20, eye_openness), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (center_x + 35, center_y - 30), 8, (50, 100, 50), -1)
        cv2.circle(frame, (center_x + 35, center_y - 30), 3, (0, 0, 0), -1)
        
        # Eyebrows with expression
        brow_height = -50
        if expression == 'focused':
            brow_height = -45  # Lower brows
        elif expression == 'tired':
            brow_height = -55  # Raised brows
        
        cv2.ellipse(frame, (center_x - 35, center_y + brow_height), (25, 5), 0, 0, 180, (100, 80, 70), -1)
        cv2.ellipse(frame, (center_x + 35, center_y + brow_height), (25, 5), 0, 0, 180, (100, 80, 70), -1)
        
        # Nose
        cv2.line(frame, (center_x, center_y - 10), (center_x, center_y + 20), (160, 150, 140), 3)
        
        # Mouth with expression
        mouth_curve = 0
        if expression == 'smile':
            mouth_curve = 20  # Upward curve
        elif expression == 'tired':
            mouth_curve = -10  # Slight frown
        
        # Draw mouth
        pts = np.array([
            [center_x - 30, center_y + 50],
            [center_x - 15, center_y + 50 + mouth_curve//2],
            [center_x, center_y + 50 + mouth_curve],
            [center_x + 15, center_y + 50 + mouth_curve//2],
            [center_x + 30, center_y + 50]
        ], np.int32)
        cv2.polylines(frame, [pts], False, (150, 100, 100), 3)
        
        return frame

def main():
    """Download and prepare real face dataset."""
    downloader = RealFaceDatasetDownloader()
    
    print("=== REAL FACE DATASET PREPARATION ===")
    print("\nAttempting multiple approaches to obtain real face videos...")
    
    all_videos = []
    
    # Approach 1: Try to download sample videos
    print("\n1. Attempting to download sample videos...")
    downloaded = downloader.download_sample_videos()
    all_videos.extend(downloaded)
    
    # Approach 2: Check for existing samples
    print("\n2. Checking for existing sample videos...")
    existing_dir, existing_videos = downloader.use_existing_samples()
    if existing_videos:
        all_videos.extend(existing_videos)
    
    # Approach 3: Create high-quality synthetic videos
    print("\n3. Creating realistic synthetic face videos...")
    synthetic = downloader.create_synthetic_face_videos()
    all_videos.extend(synthetic)
    
    # Prepare final dataset
    if all_videos:
        # Copy all videos to final dataset directory
        final_dataset = os.path.join(downloader.dataset_dir, "validation_dataset")
        os.makedirs(final_dataset, exist_ok=True)
        
        # Copy videos to final location
        import shutil
        copied_videos = []
        for video_path in all_videos:
            dest_path = os.path.join(final_dataset, os.path.basename(video_path))
            shutil.copy2(video_path, dest_path)
            copied_videos.append(dest_path)
        
        print(f"\n=== DATASET PREPARED ===")
        print(f"Total videos available: {len(all_videos)}")
        print(f"Dataset location: {final_dataset}")
        
        # Create dataset info
        dataset_info = {
            'name': 'Real and Synthetic Face Validation Dataset',
            'video_count': len(all_videos),
            'videos': [os.path.basename(v) for v in copied_videos],
            'description': 'Mixed dataset for validation testing'
        }
        
        with open(os.path.join(final_dataset, 'dataset_info.json'), 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print("\n✅ Dataset ready for validation!")
        print(f"\nRun validation with:")
        print(f"  python3 smart_validator.py {final_dataset}")
        
        return final_dataset
    else:
        print("\n❌ Could not prepare dataset automatically")
        print("\nManual steps required:")
        print("1. Download face videos from:")
        print("   - Pexels.com (free stock videos)")
        print("   - Your own webcam recordings")
        print("2. Place videos in: ./real_face_datasets/")
        print("3. Run validation")
        
        return None

if __name__ == "__main__":
    dataset_path = main()
    
    if dataset_path and os.path.exists(dataset_path):
        # Automatically run validation if dataset was created
        print("\n" + "="*60)
        print("RUNNING VALIDATION ON PREPARED DATASET")
        print("="*60)
        
        import subprocess
        subprocess.run([
            'python3', 'smart_validator.py', dataset_path, '--max-videos', '10'
        ])