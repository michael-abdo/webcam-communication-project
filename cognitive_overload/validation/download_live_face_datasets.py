#!/usr/bin/env python3
"""
Download and Test Live Face Datasets

This script downloads real human face datasets and validates our cognitive
overload detection system against actual webcam videos.
"""

import os
import subprocess
import urllib.request
import urllib.error
import zipfile
import json
import shutil
from typing import List, Dict, Tuple, Optional

class LiveFaceDatasetDownloader:
    """
    Downloads and prepares real face video datasets for validation.
    """
    
    def __init__(self, dataset_dir: str = "./live_face_datasets"):
        """Initialize downloader."""
        self.dataset_dir = dataset_dir
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # Dataset configurations
        self.datasets = [
            {
                'name': 'faces_in_event_streams',
                'description': 'FES: 689 minutes, 1.6M+ faces, 30 Hz annotations',
                'url': 'https://github.com/IS2AI/faces-in-event-streams',
                'type': 'github',
                'license': 'MIT',
                'expected_videos': 50,
                'download_method': self.download_fes_dataset
            },
            {
                'name': 'mobiface_dataset',
                'description': 'MobiFace: 80 live-streaming mobile videos, 95K+ labels',
                'url': 'https://www.idiap.ch/en/dataset/mobiface',
                'type': 'research',
                'license': 'Academic Use',
                'expected_videos': 80,
                'download_method': self.download_mobiface_dataset
            },
            {
                'name': 'selfies_videos_kaggle',
                'description': 'Selfies/Videos: 4,200+ video sets for face recognition',
                'url': 'tapakah68/selfies-and-video-dataset-4-000-people',
                'type': 'kaggle',
                'license': 'Open Database',
                'expected_videos': 4200,
                'download_method': self.download_kaggle_selfies
            },
            {
                'name': 'webcam_liveness_kaggle',
                'description': 'Webcam Liveness: 30,000+ real/fake videos, anti-spoofing',
                'url': 'webcam-face-liveness-detection-dataset',
                'type': 'kaggle',
                'license': 'Open Database',
                'expected_videos': 30000,
                'download_method': self.download_kaggle_liveness
            }
        ]
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if required tools are installed."""
        prerequisites = {}
        
        # Check git
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            prerequisites['git'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            prerequisites['git'] = False
        
        # Check kaggle
        try:
            subprocess.run(['kaggle', '--version'], capture_output=True, check=True)
            prerequisites['kaggle'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            prerequisites['kaggle'] = False
        
        # Check curl/wget
        try:
            subprocess.run(['curl', '--version'], capture_output=True, check=True)
            prerequisites['curl'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            prerequisites['curl'] = False
        
        return prerequisites
    
    def install_prerequisites(self):
        """Install missing prerequisites."""
        print("=== INSTALLING PREREQUISITES ===")
        
        prerequisites = self.check_prerequisites()
        
        if not prerequisites.get('kaggle', False):
            print("Installing Kaggle API...")
            try:
                subprocess.run(['pip', 'install', 'kaggle'], check=True)
                print("✅ Kaggle API installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install Kaggle API: {e}")
        
        # Check for Kaggle API key
        kaggle_key_path = os.path.expanduser('~/.kaggle/kaggle.json')
        if not os.path.exists(kaggle_key_path):
            print(f"\n⚠️  Kaggle API key not found at {kaggle_key_path}")
            print("To download Kaggle datasets:")
            print("1. Go to https://www.kaggle.com/account")
            print("2. Click 'Create New API Token'")
            print("3. Save kaggle.json to ~/.kaggle/")
            print("4. chmod 600 ~/.kaggle/kaggle.json")
    
    def download_fes_dataset(self, dataset_config: Dict) -> Tuple[bool, str, List[str]]:
        """Download Faces in Event Streams dataset from GitHub."""
        print(f"\n=== DOWNLOADING {dataset_config['name'].upper()} ===")
        print(f"Description: {dataset_config['description']}")
        
        repo_dir = os.path.join(self.dataset_dir, dataset_config['name'])
        
        try:
            if os.path.exists(repo_dir):
                print("Repository already exists, pulling latest...")
                subprocess.run(['git', 'pull'], cwd=repo_dir, check=True)
            else:
                print("Cloning repository...")
                subprocess.run([
                    'git', 'clone', dataset_config['url'], repo_dir
                ], check=True)
            
            # Look for video files in the repository
            video_files = []
            for root, dirs, files in os.walk(repo_dir):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        video_files.append(os.path.join(root, file))
            
            if video_files:
                print(f"✅ Found {len(video_files)} video files")
                return True, repo_dir, video_files
            else:
                print("⚠️  Repository cloned but no video files found")
                print("This may require additional download steps or dataset access request")
                return False, repo_dir, []
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading FES dataset: {e}")
            return False, "", []
    
    def download_mobiface_dataset(self, dataset_config: Dict) -> Tuple[bool, str, List[str]]:
        """Download MobiFace dataset (research access required)."""
        print(f"\n=== DOWNLOADING {dataset_config['name'].upper()} ===")
        print(f"Description: {dataset_config['description']}")
        
        print("⚠️  MobiFace dataset requires research access request")
        print(f"Please visit: {dataset_config['url']}")
        print("This dataset requires institutional affiliation and research proposal")
        
        # Create placeholder directory with instructions
        dataset_dir = os.path.join(self.dataset_dir, dataset_config['name'])
        os.makedirs(dataset_dir, exist_ok=True)
        
        instructions = {
            'dataset': 'MobiFace',
            'status': 'Manual download required',
            'url': dataset_config['url'],
            'instructions': [
                '1. Visit the dataset webpage',
                '2. Submit research access request',
                '3. Download videos to this directory when approved',
                '4. Re-run validation script'
            ]
        }
        
        with open(os.path.join(dataset_dir, 'download_instructions.json'), 'w') as f:
            json.dump(instructions, f, indent=2)
        
        return False, dataset_dir, []
    
    def download_kaggle_selfies(self, dataset_config: Dict) -> Tuple[bool, str, List[str]]:
        """Download Selfies and Videos dataset from Kaggle."""
        print(f"\n=== DOWNLOADING {dataset_config['name'].upper()} ===")
        print(f"Description: {dataset_config['description']}")
        
        dataset_dir = os.path.join(self.dataset_dir, dataset_config['name'])
        os.makedirs(dataset_dir, exist_ok=True)
        
        try:
            print("Downloading from Kaggle...")
            subprocess.run([
                'kaggle', 'datasets', 'download', 
                '-d', dataset_config['url'],
                '-p', dataset_dir,
                '--unzip'
            ], check=True)
            
            # Find video files
            video_files = []
            for root, dirs, files in os.walk(dataset_dir):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        video_files.append(os.path.join(root, file))
            
            print(f"✅ Downloaded {len(video_files)} video files")
            return True, dataset_dir, video_files[:100]  # Limit for testing
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading Kaggle selfies dataset: {e}")
            print("Make sure Kaggle API is configured correctly")
            return False, dataset_dir, []
    
    def download_kaggle_liveness(self, dataset_config: Dict) -> Tuple[bool, str, List[str]]:
        """Download Webcam Liveness dataset from Kaggle."""
        print(f"\n=== DOWNLOADING {dataset_config['name'].upper()} ===")
        print(f"Description: {dataset_config['description']}")
        
        dataset_dir = os.path.join(self.dataset_dir, dataset_config['name'])
        os.makedirs(dataset_dir, exist_ok=True)
        
        try:
            print("Downloading from Kaggle...")
            subprocess.run([
                'kaggle', 'datasets', 'download',
                '-d', dataset_config['url'],
                '-p', dataset_dir,
                '--unzip'
            ], check=True)
            
            # Find video files (focus on "real" videos for our testing)
            video_files = []
            for root, dirs, files in os.walk(dataset_dir):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        # Prioritize "real" videos over "fake" for cognitive testing
                        if 'real' in file.lower() or 'live' in file.lower():
                            video_files.append(os.path.join(root, file))
            
            if not video_files:
                # If no "real" tagged files, take all videos
                for root, dirs, files in os.walk(dataset_dir):
                    for file in files:
                        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            video_files.append(os.path.join(root, file))
            
            print(f"✅ Downloaded {len(video_files)} video files")
            return True, dataset_dir, video_files[:50]  # Limit for testing
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading Kaggle liveness dataset: {e}")
            print("Make sure Kaggle API is configured correctly")
            return False, dataset_dir, []
    
    def download_all_datasets(self) -> Dict[str, Dict]:
        """Download all available datasets."""
        print("=== LIVE FACE DATASET DOWNLOAD STARTING ===")
        
        # Install prerequisites
        self.install_prerequisites()
        
        results = {}
        
        for dataset_config in self.datasets:
            try:
                success, dataset_path, video_files = dataset_config['download_method'](dataset_config)
                
                results[dataset_config['name']] = {
                    'success': success,
                    'dataset_path': dataset_path,
                    'video_files': video_files,
                    'video_count': len(video_files),
                    'description': dataset_config['description'],
                    'license': dataset_config['license']
                }
                
                if success and video_files:
                    print(f"✅ {dataset_config['name']}: {len(video_files)} videos ready")
                else:
                    print(f"⚠️  {dataset_config['name']}: Download incomplete or manual steps required")
                    
            except Exception as e:
                print(f"❌ Error with {dataset_config['name']}: {e}")
                results[dataset_config['name']] = {
                    'success': False,
                    'error': str(e),
                    'dataset_path': '',
                    'video_files': [],
                    'video_count': 0
                }
        
        # Save download summary
        summary_file = os.path.join(self.dataset_dir, 'download_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n=== DOWNLOAD SUMMARY ===")
        total_videos = sum(r['video_count'] for r in results.values())
        successful_datasets = sum(1 for r in results.values() if r['success'])
        
        print(f"Datasets processed: {len(self.datasets)}")
        print(f"Successful downloads: {successful_datasets}")
        print(f"Total videos available: {total_videos}")
        print(f"Summary saved to: {summary_file}")
        
        return results

def run_validation_on_all_datasets(download_results: Dict[str, Dict]):
    """Run validation on all successfully downloaded datasets."""
    print("\n" + "="*60)
    print("RUNNING VALIDATION ON ALL LIVE FACE DATASETS")
    print("="*60)
    
    validation_results = {}
    
    for dataset_name, dataset_info in download_results.items():
        if not dataset_info['success'] or not dataset_info['video_files']:
            print(f"\n⏭️  Skipping {dataset_name}: No videos available")
            continue
        
        print(f"\n{'='*50}")
        print(f"VALIDATING: {dataset_name.upper()}")
        print(f"Description: {dataset_info['description']}")
        print(f"Videos: {dataset_info['video_count']}")
        print(f"{'='*50}")
        
        dataset_path = dataset_info['dataset_path']
        
        try:
            # Run smart validation
            print("Running smart validation...")
            result = subprocess.run([
                'python3', 'smart_validator.py', dataset_path, '--max-videos', '20'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Smart validation completed successfully")
                validation_results[dataset_name] = {
                    'smart_validation': 'success',
                    'output': result.stdout
                }
            else:
                print(f"⚠️  Smart validation had issues: {result.stderr}")
                validation_results[dataset_name] = {
                    'smart_validation': 'partial',
                    'output': result.stdout,
                    'error': result.stderr
                }
            
            # If smart validation suggests low detection, run adaptive validation
            if 'detection rate' in result.stdout.lower() and any(
                rate in result.stdout.lower() for rate in ['0%', '10%', '20%', '30%', '40%', '50%', '60%']
            ):
                print("Detection rate appears low, running adaptive validation...")
                
                adaptive_result = subprocess.run([
                    'python3', 'adaptive_validator.py', dataset_path, 
                    '--target-rate', '0.7', '--max-videos', '10'
                ], capture_output=True, text=True, timeout=600)
                
                validation_results[dataset_name]['adaptive_validation'] = {
                    'success': adaptive_result.returncode == 0,
                    'output': adaptive_result.stdout,
                    'error': adaptive_result.stderr if adaptive_result.returncode != 0 else None
                }
            
        except subprocess.TimeoutExpired:
            print(f"❌ Validation timeout for {dataset_name}")
            validation_results[dataset_name] = {
                'smart_validation': 'timeout',
                'error': 'Validation process timed out'
            }
        except Exception as e:
            print(f"❌ Error validating {dataset_name}: {e}")
            validation_results[dataset_name] = {
                'smart_validation': 'error',
                'error': str(e)
            }
    
    # Save validation results
    results_file = './live_face_datasets/validation_results_summary.json'
    with open(results_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n✅ All validation results saved to: {results_file}")
    return validation_results

def main():
    """Main execution function."""
    print("LIVE FACE DATASET VALIDATION SYSTEM")
    print("Testing cognitive overload detection with real human faces")
    print("="*60)
    
    # Download datasets
    downloader = LiveFaceDatasetDownloader()
    download_results = downloader.download_all_datasets()
    
    # Run validation on successfully downloaded datasets
    if any(r['success'] for r in download_results.values()):
        validation_results = run_validation_on_all_datasets(download_results)
        
        # Print final summary
        print("\n" + "="*60)
        print("FINAL RESULTS SUMMARY")
        print("="*60)
        
        for dataset_name, result in validation_results.items():
            status = "✅ SUCCESS" if result.get('smart_validation') == 'success' else "⚠️  PARTIAL/ISSUES"
            print(f"{dataset_name}: {status}")
        
        print(f"\nDetailed results available in:")
        print(f"- ./live_face_datasets/download_summary.json")
        print(f"- ./live_face_datasets/validation_results_summary.json")
        
    else:
        print("\n❌ No datasets were successfully downloaded")
        print("Check the download summary for manual download instructions")

if __name__ == "__main__":
    main()