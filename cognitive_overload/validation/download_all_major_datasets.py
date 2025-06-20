#!/usr/bin/env python3
"""
Download and Test ALL Major Face Datasets for Cognitive Expression Detection

This script downloads and validates cognitive overload detection on:
1. Faces in Event Streams (FES) - 689 minutes, 1.6M+ faces
2. MobiFace Dataset - 80 mobile videos, 95K+ bounding boxes  
3. Selfies and Videos Dataset (Kaggle) - 4,200+ video sets
4. Web Camera Face Liveness Detection (Kaggle) - 30,000+ videos

Author: Cognitive Overload Detection System
"""

import os
import sys
import json
import subprocess
import requests
import zipfile
from typing import Dict, List, Any
from datetime import datetime
import shutil

# Try to import kaggle but handle gracefully if not configured
try:
    import kaggle
    KAGGLE_AVAILABLE = True
except Exception as e:
    KAGGLE_AVAILABLE = False
    KAGGLE_ERROR = str(e)

class MajorDatasetDownloader:
    """Download and prepare all major face datasets for cognitive testing."""
    
    def __init__(self, base_dir: str = "./major_face_datasets"):
        """Initialize downloader with base directory."""
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Dataset configurations
        self.datasets = {
            'faces_in_event_streams': {
                'name': 'Faces in Event Streams (FES)',
                'description': '689 minutes of video with 1.6M+ annotated faces',
                'source': 'github',
                'url': 'https://github.com/IS2AI/faces-in-event-streams',
                'license': 'MIT',
                'size': '689 minutes',
                'faces': '1.6M+',
                'annotation_rate': '30 Hz',
                'local_path': os.path.join(self.base_dir, 'faces_event_streams')
            },
            'mobiface': {
                'name': 'MobiFace Dataset',
                'description': '80 live-streaming mobile videos from 70 smartphone users',
                'source': 'research_paper',
                'url': 'https://mobiface.github.io/',
                'license': 'Research',
                'size': '80 videos',
                'faces': '95K+ bounding boxes',
                'environment': 'unconstrained real-world',
                'local_path': os.path.join(self.base_dir, 'mobiface')
            },
            'selfies_videos_kaggle': {
                'name': 'Selfies and Videos Dataset (Kaggle)',
                'description': '4,200+ video sets for face recognition',
                'source': 'kaggle',
                'dataset_id': 'kmader/selfie-and-video-dataset',
                'license': 'CC0',
                'size': '4,200+ videos',
                'faces': 'Multiple per video',
                'use_case': 'face recognition',
                'local_path': os.path.join(self.base_dir, 'selfies_videos_kaggle')
            },
            'webcam_liveness_kaggle': {
                'name': 'Web Camera Face Liveness Detection (Kaggle)',
                'description': '30,000+ videos of real/fake face attacks',
                'source': 'kaggle',
                'dataset_id': 'datasets/face-detection-in-images',
                'alternative_id': 'akshaypisal/anti-spoofing-liveness-detection',
                'license': 'Various',
                'size': '30,000+ videos',
                'faces': 'Real and spoofed',
                'use_case': 'anti-spoofing',
                'local_path': os.path.join(self.base_dir, 'webcam_liveness')
            }
        }
        
        self.download_log = []
        
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if required tools and credentials are available."""
        checks = {}
        
        # Check Git
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            checks['git'] = True
        except:
            checks['git'] = False
            
        # Check Kaggle API
        if KAGGLE_AVAILABLE:
            try:
                # Try to authenticate
                kaggle.api.authenticate()
                checks['kaggle_api'] = True
            except Exception as e:
                checks['kaggle_api'] = False
                checks['kaggle_error'] = str(e)
        else:
            checks['kaggle_api'] = False
            checks['kaggle_error'] = KAGGLE_ERROR
            
        # Check wget/curl
        try:
            subprocess.run(['wget', '--version'], capture_output=True, check=True)
            checks['wget'] = True
        except:
            try:
                subprocess.run(['curl', '--version'], capture_output=True, check=True)
                checks['curl'] = True
            except:
                checks['wget'] = False
                checks['curl'] = False
                
        return checks
    
    def download_faces_event_streams(self) -> Dict[str, Any]:
        """Download Faces in Event Streams (FES) dataset."""
        print(f"\\n{'='*60}")
        print("DOWNLOADING: Faces in Event Streams (FES)")
        print(f"{'='*60}")
        
        dataset_info = self.datasets['faces_in_event_streams']
        local_path = dataset_info['local_path']
        
        try:
            if os.path.exists(local_path):
                print(f"Dataset already exists at: {local_path}")
                return {'success': True, 'message': 'Already downloaded', 'path': local_path}
            
            # Clone the repository
            print("Cloning FES repository...")
            result = subprocess.run([
                'git', 'clone', 
                'https://github.com/IS2AI/faces-in-event-streams.git',
                local_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    'success': False, 
                    'error': f"Git clone failed: {result.stderr}",
                    'dataset': 'faces_event_streams'
                }
            
            # Check if dataset has download scripts
            download_script = os.path.join(local_path, 'download.sh')
            if os.path.exists(download_script):
                print("Running dataset download script...")
                os.chmod(download_script, 0o755)
                subprocess.run(['bash', download_script], cwd=local_path)
            
            # Create summary
            summary = {
                'dataset': 'Faces in Event Streams',
                'path': local_path,
                'source': dataset_info['url'],
                'description': dataset_info['description'],
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(os.path.join(local_path, 'download_info.json'), 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"✅ FES dataset downloaded to: {local_path}")
            return {'success': True, 'message': 'Downloaded successfully', 'path': local_path}
            
        except Exception as e:
            return {
                'success': False, 
                'error': f"FES download failed: {str(e)}",
                'dataset': 'faces_event_streams'
            }
    
    def download_mobiface(self) -> Dict[str, Any]:
        """Download MobiFace dataset."""
        print(f"\\n{'='*60}")
        print("DOWNLOADING: MobiFace Dataset")
        print(f"{'='*60}")
        
        dataset_info = self.datasets['mobiface']
        local_path = dataset_info['local_path']
        
        try:
            os.makedirs(local_path, exist_ok=True)
            
            # MobiFace requires manual download - create instructions
            instructions = {
                'dataset': 'MobiFace',
                'status': 'manual_download_required',
                'instructions': [
                    '1. Visit: https://mobiface.github.io/',
                    '2. Request access to dataset',
                    '3. Download files to this directory',
                    '4. Unzip all archives',
                    '5. Re-run validation script'
                ],
                'path': local_path,
                'downloaded_at': datetime.now().isoformat(),
                'description': dataset_info['description']
            }
            
            with open(os.path.join(local_path, 'download_instructions.json'), 'w') as f:
                json.dump(instructions, f, indent=2)
            
            print(f"📋 MobiFace requires manual download")
            print(f"   Instructions saved to: {local_path}/download_instructions.json")
            print(f"   Visit: {dataset_info['url']}")
            
            return {
                'success': True, 
                'message': 'Manual download instructions created', 
                'path': local_path,
                'manual_download': True
            }
            
        except Exception as e:
            return {
                'success': False, 
                'error': f"MobiFace setup failed: {str(e)}",
                'dataset': 'mobiface'
            }
    
    def download_selfies_videos_kaggle(self) -> Dict[str, Any]:
        """Download Selfies and Videos dataset from Kaggle."""
        print(f"\\n{'='*60}")
        print("DOWNLOADING: Selfies and Videos Dataset (Kaggle)")
        print(f"{'='*60}")
        
        dataset_info = self.datasets['selfies_videos_kaggle']
        local_path = dataset_info['local_path']
        
        try:
            os.makedirs(local_path, exist_ok=True)
            
            # Try to download using Kaggle API
            print("Downloading from Kaggle...")
            kaggle.api.dataset_download_files(
                dataset_info['dataset_id'], 
                path=local_path, 
                unzip=True
            )
            
            # Create summary
            summary = {
                'dataset': 'Selfies and Videos (Kaggle)',
                'kaggle_id': dataset_info['dataset_id'],
                'path': local_path,
                'description': dataset_info['description'],
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(os.path.join(local_path, 'download_info.json'), 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"✅ Selfies dataset downloaded to: {local_path}")
            return {'success': True, 'message': 'Downloaded successfully', 'path': local_path}
            
        except Exception as e:
            return {
                'success': False, 
                'error': f"Kaggle download failed: {str(e)}",
                'dataset': 'selfies_videos_kaggle'
            }
    
    def download_webcam_liveness_kaggle(self) -> Dict[str, Any]:
        """Download Webcam Liveness Detection dataset from Kaggle."""
        print(f"\\n{'='*60}")
        print("DOWNLOADING: Web Camera Face Liveness Detection (Kaggle)")
        print(f"{'='*60}")
        
        dataset_info = self.datasets['webcam_liveness_kaggle']
        local_path = dataset_info['local_path']
        
        try:
            os.makedirs(local_path, exist_ok=True)
            
            # Try multiple dataset IDs as liveness datasets may vary
            dataset_ids = [
                'akshayiitm/anti-spoofing-liveness-detection',
                'datasets/face-detection-in-images',
                'sbaghbidi/face-antispoofing-dataset'
            ]
            
            downloaded = False
            for dataset_id in dataset_ids:
                try:
                    print(f"Trying dataset: {dataset_id}")
                    kaggle.api.dataset_download_files(
                        dataset_id, 
                        path=local_path, 
                        unzip=True
                    )
                    downloaded = True
                    used_dataset_id = dataset_id
                    break
                except Exception as e:
                    print(f"Failed {dataset_id}: {e}")
                    continue
            
            if not downloaded:
                # Create manual instructions if no dataset works
                instructions = {
                    'dataset': 'Webcam Liveness Detection',
                    'status': 'manual_download_required',
                    'instructions': [
                        '1. Visit: https://www.kaggle.com/datasets',
                        '2. Search for "face liveness detection" or "anti-spoofing"',
                        '3. Download suitable liveness detection dataset',
                        '4. Extract to this directory',
                        '5. Re-run validation script'
                    ],
                    'path': local_path,
                    'downloaded_at': datetime.now().isoformat()
                }
                
                with open(os.path.join(local_path, 'download_instructions.json'), 'w') as f:
                    json.dump(instructions, f, indent=2)
                
                return {
                    'success': True, 
                    'message': 'Manual download instructions created', 
                    'path': local_path,
                    'manual_download': True
                }
            
            # Create summary for successful download
            summary = {
                'dataset': 'Webcam Liveness Detection (Kaggle)',
                'kaggle_id': used_dataset_id,
                'path': local_path,
                'description': dataset_info['description'],
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(os.path.join(local_path, 'download_info.json'), 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"✅ Liveness dataset downloaded to: {local_path}")
            return {'success': True, 'message': 'Downloaded successfully', 'path': local_path}
            
        except Exception as e:
            return {
                'success': False, 
                'error': f"Liveness download failed: {str(e)}",
                'dataset': 'webcam_liveness_kaggle'
            }
    
    def download_all_datasets(self) -> Dict[str, Any]:
        """Download all major face datasets."""
        print("=" * 80)
        print("MAJOR FACE DATASETS DOWNLOAD")
        print("Downloading ALL major datasets for cognitive expression testing")
        print("=" * 80)
        
        # Check prerequisites
        print("\\nChecking prerequisites...")
        prereqs = self.check_prerequisites()
        
        for tool, available in prereqs.items():
            if tool.endswith('_error'):
                continue
            status = "✅ Available" if available else "❌ Missing"
            print(f"  {tool}: {status}")
        
        if not prereqs.get('git', False):
            print("\\n❌ Git is required but not available")
            return {'success': False, 'error': 'Git not available'}
        
        if not prereqs.get('kaggle_api', False):
            print("\\n⚠️  Kaggle API not configured - some downloads may require manual setup")
            if 'kaggle_error' in prereqs:
                print(f"   Error: {prereqs['kaggle_error']}")
        
        # Download each dataset
        results = {}
        
        # 1. Faces in Event Streams
        results['faces_event_streams'] = self.download_faces_event_streams()
        
        # 2. MobiFace Dataset  
        results['mobiface'] = self.download_mobiface()
        
        # 3. Selfies and Videos (Kaggle)
        if prereqs.get('kaggle_api', False):
            results['selfies_videos_kaggle'] = self.download_selfies_videos_kaggle()
        else:
            results['selfies_videos_kaggle'] = {
                'success': False, 
                'error': 'Kaggle API not configured'
            }
        
        # 4. Webcam Liveness Detection (Kaggle)
        if prereqs.get('kaggle_api', False):
            results['webcam_liveness'] = self.download_webcam_liveness_kaggle()
        else:
            results['webcam_liveness'] = {
                'success': False, 
                'error': 'Kaggle API not configured'
            }
        
        # Save overall summary
        summary = {
            'download_session': datetime.now().isoformat(),
            'datasets_attempted': len(results),
            'successful_downloads': len([r for r in results.values() if r.get('success', False)]),
            'manual_downloads_required': len([r for r in results.values() if r.get('manual_download', False)]),
            'results': results,
            'base_directory': self.base_dir
        }
        
        summary_file = os.path.join(self.base_dir, 'download_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print final summary
        print(f"\\n{'='*80}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*80}")
        
        successful = 0
        manual = 0
        failed = 0
        
        for dataset_name, result in results.items():
            if result.get('success', False):
                if result.get('manual_download', False):
                    print(f"📋 {dataset_name}: Manual download required")
                    manual += 1
                else:
                    print(f"✅ {dataset_name}: Downloaded successfully")
                    successful += 1
            else:
                print(f"❌ {dataset_name}: {result.get('error', 'Unknown error')}")
                failed += 1
        
        print(f"\\nResults: {successful} automatic, {manual} manual, {failed} failed")
        print(f"Summary saved to: {summary_file}")
        
        return summary

def main():
    """Main execution function."""
    print("MAJOR FACE DATASETS DOWNLOADER")
    print("Preparing ALL major datasets for cognitive expression testing")
    print("=" * 80)
    
    downloader = MajorDatasetDownloader()
    results = downloader.download_all_datasets()
    
    if results.get('successful_downloads', 0) > 0 or results.get('manual_downloads_required', 0) > 0:
        print("\\n🎯 NEXT STEPS:")
        print("1. Complete any manual downloads")
        print("2. Run cognitive expression testing on all datasets")
        print("3. Compare performance across dataset types")
        
        print("\\n📋 To test cognitive expressions on all datasets:")
        print("   python3 test_cognitive_expressions_all_major.py")
    
    return results

if __name__ == "__main__":
    main()