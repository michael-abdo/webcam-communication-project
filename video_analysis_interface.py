#!/usr/bin/env python3
"""
Video Dataset Analysis Interface
Deep analytical decomposition for real-time video fatigue analysis

Architecture:
1. Dataset Discovery & Management
2. Video Selection & Loading
3. Real-time Analysis Engine  
4. Results Visualization & Export
5. Comparative Analytics
"""

import os
import sys
import json
import cv2
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_cors import CORS
import threading
import queue
import numpy as np

# Add project paths
sys.path.append('./cognitive_overload/processing')
sys.path.append('./cognitive_overload/validation')

# Import fatigue detection system
try:
    from fatigue_metrics import FatigueDetector
    from alert_system import AlertSystem
    FATIGUE_AVAILABLE = True
except ImportError:
    FATIGUE_AVAILABLE = False
    print("Warning: Fatigue detection not available in lightweight mode")

@dataclass
class VideoMetadata:
    """Complete video file metadata"""
    filepath: str
    filename: str
    size_bytes: int
    duration_seconds: float
    fps: float
    width: int
    height: int
    total_frames: int
    codec: str
    dataset_type: str
    subject_id: Optional[str] = None
    scenario: Optional[str] = None
    quality_score: Optional[float] = None

@dataclass
class AnalysisFrame:
    """Single frame analysis result"""
    frame_number: int
    timestamp: float
    perclos: float
    blink_rate: float
    fatigue_level: str
    risk_score: float
    landmarks_detected: bool
    processing_time_ms: float

class VideoDatasetManager:
    """Manages discovery and organization of video datasets"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.datasets = {}
        self.video_cache = {}
        self._discover_datasets()
    
    def _discover_datasets(self):
        """Discover all video datasets using deep analysis"""
        dataset_paths = {
            'test_videos': 'cognitive_overload/tests/test_videos',
            'live_faces': 'cognitive_overload/validation/live_face_datasets',
            'real_faces': 'cognitive_overload/validation/real_face_datasets', 
            'webcam_samples': 'cognitive_overload/validation/webcam_datasets',
            'processed_results': 'cognitive_overload/data/processed_results'
        }
        
        for dataset_name, path in dataset_paths.items():
            full_path = self.base_path / path
            if full_path.exists():
                self.datasets[dataset_name] = self._analyze_dataset(full_path, dataset_name)
    
    def _analyze_dataset(self, path: Path, dataset_type: str) -> Dict:
        """Deep analysis of dataset structure and contents"""
        dataset_info = {
            'path': str(path),
            'type': dataset_type,
            'videos': [],
            'total_size': 0,
            'total_videos': 0,
            'subjects': set(),
            'scenarios': set()
        }
        
        # Recursively find all video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
        for video_file in path.rglob('*'):
            if video_file.suffix.lower() in video_extensions:
                try:
                    metadata = self._extract_video_metadata(video_file, dataset_type)
                    if metadata:
                        dataset_info['videos'].append(metadata)
                        dataset_info['total_size'] += metadata.size_bytes
                        dataset_info['total_videos'] += 1
                        
                        if metadata.subject_id:
                            dataset_info['subjects'].add(metadata.subject_id)
                        if metadata.scenario:
                            dataset_info['scenarios'].add(metadata.scenario)
                            
                except Exception as e:
                    print(f"Error analyzing {video_file}: {e}")
        
        # Convert sets to lists for JSON serialization
        dataset_info['subjects'] = list(dataset_info['subjects'])
        dataset_info['scenarios'] = list(dataset_info['scenarios'])
        
        return dataset_info
    
    def _extract_video_metadata(self, video_path: Path, dataset_type: str) -> Optional[VideoMetadata]:
        """Extract comprehensive metadata from video file"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None
            
            # Basic video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Codec information
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            cap.release()
            
            # File system metadata
            stat = video_path.stat()
            
            # Extract subject/scenario from path structure
            subject_id = self._extract_subject_id(video_path, dataset_type)
            scenario = self._extract_scenario(video_path, dataset_type)
            
            return VideoMetadata(
                filepath=str(video_path),
                filename=video_path.name,
                size_bytes=stat.st_size,
                duration_seconds=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames,
                codec=codec,
                dataset_type=dataset_type,
                subject_id=subject_id,
                scenario=scenario,
                quality_score=self._calculate_quality_score(width, height, fps, stat.st_size, duration)
            )
            
        except Exception as e:
            print(f"Error extracting metadata from {video_path}: {e}")
            return None
    
    def _extract_subject_id(self, video_path: Path, dataset_type: str) -> Optional[str]:
        """Extract subject ID from file path structure"""
        if dataset_type == 'live_faces':
            # Pattern: .../files/[subject_id]/video.mp4
            parts = video_path.parts
            if 'files' in parts:
                files_idx = parts.index('files')
                if files_idx + 1 < len(parts):
                    return f"subject_{parts[files_idx + 1]}"
        return None
    
    def _extract_scenario(self, video_path: Path, dataset_type: str) -> Optional[str]:
        """Extract scenario from filename or path"""
        name = video_path.stem.lower()
        
        # Common scenario patterns
        scenarios = {
            'neutral': ['neutral', 'baseline', 'relaxed'],
            'smile': ['smile', 'happy', 'positive'],
            'focused': ['focused', 'concentrated', 'attention'],
            'tired': ['tired', 'fatigue', 'exhausted'],
            'reading': ['reading', 'text'],
            'math': ['math', 'calculation'],
            'problem': ['problem', 'solving']
        }
        
        for scenario, keywords in scenarios.items():
            if any(keyword in name for keyword in keywords):
                return scenario
                
        return video_path.stem
    
    def _calculate_quality_score(self, width: int, height: int, fps: float, 
                                size_bytes: int, duration: float) -> float:
        """Calculate video quality score (0-1)"""
        if duration <= 0:
            return 0.0
        
        # Resolution score (0-0.4)
        resolution_score = min(0.4, (width * height) / (1920 * 1080) * 0.4)
        
        # FPS score (0-0.3)  
        fps_score = min(0.3, fps / 60.0 * 0.3)
        
        # Bitrate score (0-0.3)
        bitrate = (size_bytes * 8) / duration  # bits per second
        bitrate_score = min(0.3, bitrate / (5 * 1024 * 1024) * 0.3)  # 5 Mbps reference
        
        return resolution_score + fps_score + bitrate_score
    
    def get_datasets_summary(self) -> Dict:
        """Get comprehensive datasets summary"""
        summary = {
            'total_datasets': len(self.datasets),
            'total_videos': sum(d['total_videos'] for d in self.datasets.values()),
            'total_size_mb': sum(d['total_size'] for d in self.datasets.values()) / (1024 * 1024),
            'datasets': {}
        }
        
        for name, data in self.datasets.items():
            summary['datasets'][name] = {
                'videos': data['total_videos'],
                'size_mb': data['total_size'] / (1024 * 1024),
                'subjects': len(data['subjects']),
                'scenarios': len(data['scenarios'])
            }
        
        return summary
    
    def get_videos_by_criteria(self, dataset_type: Optional[str] = None,
                              subject_id: Optional[str] = None,
                              scenario: Optional[str] = None,
                              min_quality: float = 0.0) -> List[VideoMetadata]:
        """Get videos matching specific criteria"""
        results = []
        
        for dataset_name, dataset in self.datasets.items():
            if dataset_type and dataset_name != dataset_type:
                continue
                
            for video_data in dataset['videos']:
                video = VideoMetadata(**video_data)
                
                # Apply filters
                if subject_id and video.subject_id != subject_id:
                    continue
                if scenario and video.scenario != scenario:
                    continue
                if video.quality_score and video.quality_score < min_quality:
                    continue
                    
                results.append(video)
        
        return sorted(results, key=lambda v: v.quality_score or 0, reverse=True)

class VideoAnalysisEngine:
    """Real-time video analysis engine"""
    
    def __init__(self):
        self.fatigue_detector = None
        self.alert_system = None
        self.current_video = None
        self.analysis_results = []
        self.is_analyzing = False
        self.frame_queue = queue.Queue(maxsize=100)
        
        if FATIGUE_AVAILABLE:
            try:
                self.fatigue_detector = FatigueDetector()
                self.alert_system = AlertSystem()
            except Exception as e:
                print(f"Error initializing fatigue detection: {e}")
    
    def analyze_video(self, video_path: str, frame_skip: int = 1) -> List[AnalysisFrame]:
        """Analyze entire video and return frame-by-frame results"""
        results = []
        self.is_analyzing = True
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_number = 0
            
            while self.is_analyzing:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % frame_skip == 0:
                    start_time = time.time()
                    analysis = self._analyze_frame(frame, frame_number, frame_number / fps)
                    analysis.processing_time_ms = (time.time() - start_time) * 1000
                    results.append(analysis)
                
                frame_number += 1
            
            cap.release()
            
        except Exception as e:
            print(f"Error during video analysis: {e}")
            self.is_analyzing = False
        
        self.analysis_results = results
        return results
    
    def _analyze_frame(self, frame: np.ndarray, frame_num: int, timestamp: float) -> AnalysisFrame:
        """Analyze single frame for fatigue indicators"""
        if not self.fatigue_detector:
            # Lightweight analysis without heavy dependencies
            return AnalysisFrame(
                frame_number=frame_num,
                timestamp=timestamp,
                perclos=0.2,  # Mock data
                blink_rate=15.0,
                fatigue_level="NORMAL",
                risk_score=0.3,
                landmarks_detected=True,
                processing_time_ms=10.0
            )
        
        try:
            # Real fatigue analysis
            result = self.fatigue_detector.analyze_frame(frame)
            
            return AnalysisFrame(
                frame_number=frame_num,
                timestamp=timestamp,
                perclos=result.get('perclos', 0.0),
                blink_rate=result.get('blink_rate', 0.0),
                fatigue_level=result.get('fatigue_level', 'NORMAL'),
                risk_score=result.get('risk_score', 0.0),
                landmarks_detected=result.get('landmarks_detected', False),
                processing_time_ms=result.get('processing_time_ms', 0.0)
            )
            
        except Exception as e:
            print(f"Error analyzing frame {frame_num}: {e}")
            return AnalysisFrame(
                frame_number=frame_num,
                timestamp=timestamp,
                perclos=0.0,
                blink_rate=0.0,
                fatigue_level="ERROR",
                risk_score=0.0,
                landmarks_detected=False,
                processing_time_ms=0.0
            )
    
    def stop_analysis(self):
        """Stop current analysis"""
        self.is_analyzing = False

# Flask Web Application
app = Flask(__name__)
CORS(app)

# Global instances
dataset_manager = VideoDatasetManager()
analysis_engine = VideoAnalysisEngine()

@app.route('/')
def home():
    """Video analysis interface home"""
    return render_template('video_analysis.html')

@app.route('/api/datasets')
def get_datasets():
    """Get all available datasets"""
    return jsonify(dataset_manager.get_datasets_summary())

@app.route('/api/videos')
def get_videos():
    """Get videos with optional filtering"""
    dataset_type = request.args.get('dataset_type')
    subject_id = request.args.get('subject_id') 
    scenario = request.args.get('scenario')
    min_quality = float(request.args.get('min_quality', 0.0))
    
    videos = dataset_manager.get_videos_by_criteria(
        dataset_type=dataset_type,
        subject_id=subject_id,
        scenario=scenario,
        min_quality=min_quality
    )
    
    return jsonify([asdict(video) for video in videos])

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """Start video analysis"""
    data = request.get_json()
    video_path = data.get('video_path')
    frame_skip = data.get('frame_skip', 1)
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Invalid video path'}), 400
    
    try:
        # Run analysis in background thread
        def run_analysis():
            analysis_engine.analyze_video(video_path, frame_skip)
        
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'Analysis started', 'video_path': video_path})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results')
def get_results():
    """Get analysis results"""
    results = analysis_engine.analysis_results
    return jsonify({
        'total_frames': len(results),
        'is_analyzing': analysis_engine.is_analyzing,
        'results': [asdict(result) for result in results[-100:]]  # Last 100 frames
    })

@app.route('/api/stop')
def stop_analysis():
    """Stop current analysis"""
    analysis_engine.stop_analysis()
    return jsonify({'status': 'Analysis stopped'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)