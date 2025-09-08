#!/usr/bin/env python3
"""
Baseline Analyzer for Face and Speech Data

Processes captured baseline data to extract personalized metrics:
- Face landmark analysis for baseline facial expressions
- Eye openness, blink rate, and facial movement baselines
- Speech analysis for pitch, tone, speaking rate baselines
- Statistical compilation and validation

Author: Baseline Capture System
Version: 1.0
"""

import numpy as np
import cv2
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# Import existing landmark processor
sys.path.append(os.path.join(os.path.dirname(__file__), '../../cognitive_overload/processing'))
try:
    from landmark_processor import LandmarkProcessor
except ImportError:
    logging.warning("LandmarkProcessor not available - face analysis will be limited")
    LandmarkProcessor = None


@dataclass
class BaselineMetrics:
    """Container for compiled baseline metrics"""
    face_metrics: Dict[str, Any]
    speech_metrics: Dict[str, Any] 
    overall_quality: Dict[str, Any]
    statistical_summary: Dict[str, Any]
    created_at: str
    session_id: str


class BaselineAnalyzer:
    """
    Analyzes captured baseline data to extract personalized behavioral metrics.
    
    Processes face and speech baselines to create user-specific thresholds
    for assessment personalization according to SOP requirements.
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize baseline analyzer.
        
        Args:
            session_id (str): Session identifier for tracking
        """
        self.session_id = session_id
        self.logger = logging.getLogger(__name__)
        
        # Landmark indices for key facial features (MediaPipe Face Mesh)
        self.FACIAL_LANDMARKS = {
            # Eye regions for openness calculation
            'left_eye': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'right_eye': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
            
            # Key eye points for EAR (Eye Aspect Ratio) calculation
            'left_eye_key': [33, 160, 158, 133, 153, 144],  # Outer, top, bottom, inner, top, bottom
            'right_eye_key': [362, 385, 387, 263, 373, 380],
            
            # Eyebrow region for expression analysis
            'left_eyebrow': [46, 53, 52, 51, 48],
            'right_eyebrow': [276, 283, 282, 281, 278],
            
            # Mouth region for expression and speech analysis
            'mouth_outer': [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318],
            'mouth_inner': [78, 81, 13, 311, 308, 324, 318, 14, 87, 317, 402, 318],
            
            # Nose region for reference points
            'nose_tip': [1, 2, 5, 4, 6, 168],
        }
    
    def analyze_face_baseline(self, video_path: str, duration_seconds: float = 10) -> Dict[str, Any]:
        """
        Analyze face baseline video to extract facial behavior metrics.
        
        Args:
            video_path (str): Path to baseline face video
            duration_seconds (float): Expected duration of baseline
            
        Returns:
            Dict with face baseline metrics
        """
        try:
            self.logger.info(f"Analyzing face baseline: {video_path}")
            
            if not LandmarkProcessor:
                # Fallback analysis without MediaPipe
                return self._fallback_face_analysis(video_path, duration_seconds)
            
            face_metrics = {
                'video_path': video_path,
                'duration_seconds': duration_seconds,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Process video with MediaPipe
            with LandmarkProcessor(video_path) as processor:
                results = processor.process_video(frame_interval=1)
                
                if not results['success']:
                    raise Exception(f"Face processing failed: {results}")
                
                landmarks_data = results['landmarks_data']
                
                if not landmarks_data:
                    raise Exception("No face landmarks detected in baseline video")
                
                # Extract baseline metrics
                eye_metrics = self._analyze_eye_baseline(landmarks_data)
                expression_metrics = self._analyze_expression_baseline(landmarks_data)
                stability_metrics = self._analyze_face_stability(landmarks_data)
                
                face_metrics.update({
                    'eye_baseline': eye_metrics,
                    'expression_baseline': expression_metrics,
                    'stability_metrics': stability_metrics,
                    'total_frames': len(landmarks_data),
                    'frames_with_faces': len([f for f in landmarks_data if f['face_detected']]),
                    'face_detection_rate': len([f for f in landmarks_data if f['face_detected']]) / len(landmarks_data)
                })
                
                self.logger.info(f"Face baseline analysis complete: {len(landmarks_data)} frames processed")
                return face_metrics
                
        except Exception as e:
            self.logger.error(f"Face baseline analysis error: {e}")
            return {
                'error': str(e),
                'video_path': video_path,
                'analysis_failed': True
            }
    
    def _analyze_eye_baseline(self, landmarks_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate eye openness and blink rate baselines.
        
        Args:
            landmarks_data (List): Frame-by-frame landmark data
            
        Returns:
            Dict with eye baseline metrics
        """
        try:
            ear_values = []  # Eye Aspect Ratio values
            blink_events = []
            
            for frame_data in landmarks_data:
                if not frame_data['face_detected']:
                    continue
                
                landmarks = frame_data['landmarks']
                if len(landmarks) < 468:  # Full MediaPipe face mesh
                    continue
                
                # Calculate Eye Aspect Ratio (EAR) for both eyes
                left_ear = self._calculate_eye_aspect_ratio(landmarks, 'left_eye_key')
                right_ear = self._calculate_eye_aspect_ratio(landmarks, 'right_eye_key')
                
                # Average EAR for both eyes
                avg_ear = (left_ear + right_ear) / 2.0
                ear_values.append(avg_ear)
                
                # Detect blink (EAR drops below threshold)
                if len(ear_values) > 1:
                    if ear_values[-2] > 0.25 and avg_ear < 0.2:  # Blink detected
                        blink_events.append({
                            'frame': len(ear_values) - 1,
                            'timestamp': frame_data.get('timestamp', 0),
                            'ear_value': avg_ear
                        })
            
            if not ear_values:
                return {'error': 'No valid eye data found'}
            
            # Calculate baseline metrics
            baseline_ear = np.mean(ear_values)
            ear_std = np.std(ear_values)
            blink_rate = len(blink_events) / (len(ear_values) / 30.0)  # Assume 30 FPS
            
            return {
                'baseline_eye_openness': float(baseline_ear),
                'eye_openness_std': float(ear_std),
                'baseline_blink_rate': float(blink_rate),
                'total_blinks': len(blink_events),
                'eye_aspect_ratios': ear_values[:100],  # Store first 100 for reference
                'blink_events': blink_events[:10]  # Store first 10 blinks
            }
            
        except Exception as e:
            self.logger.error(f"Eye baseline analysis error: {e}")
            return {'error': str(e)}
    
    def _calculate_eye_aspect_ratio(self, landmarks: List[Dict], eye_key: str) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection.
        
        Args:
            landmarks (List): Face landmarks for current frame
            eye_key (str): Key for eye landmark indices
            
        Returns:
            float: Eye aspect ratio value
        """
        try:
            eye_indices = self.FACIAL_LANDMARKS[eye_key]
            eye_points = []
            
            for idx in eye_indices:
                if idx < len(landmarks):
                    eye_points.append((landmarks[idx]['x'], landmarks[idx]['y']))
            
            if len(eye_points) < 6:
                return 0.3  # Default neutral value
            
            # EAR calculation: vertical distances / horizontal distance
            # Vertical distances
            v1 = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            v2 = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            
            # Horizontal distance
            h = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            
            if h == 0:
                return 0.3
            
            ear = (v1 + v2) / (2.0 * h)
            return ear
            
        except Exception as e:
            self.logger.error(f"EAR calculation error: {e}")
            return 0.3  # Default neutral value
    
    def _analyze_expression_baseline(self, landmarks_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze baseline facial expressions and micro-expressions.
        
        Args:
            landmarks_data (List): Frame-by-frame landmark data
            
        Returns:
            Dict with expression baseline metrics
        """
        try:
            eyebrow_positions = []
            mouth_positions = []
            
            for frame_data in landmarks_data:
                if not frame_data['face_detected']:
                    continue
                
                landmarks = frame_data['landmarks']
                if len(landmarks) < 468:
                    continue
                
                # Analyze eyebrow position (indicator of surprise, concern)
                eyebrow_height = self._calculate_eyebrow_height(landmarks)
                eyebrow_positions.append(eyebrow_height)
                
                # Analyze mouth position (neutral expression baseline)
                mouth_curvature = self._calculate_mouth_curvature(landmarks)
                mouth_positions.append(mouth_curvature)
            
            if not eyebrow_positions or not mouth_positions:
                return {'error': 'Insufficient expression data'}
            
            return {
                'baseline_eyebrow_height': float(np.mean(eyebrow_positions)),
                'eyebrow_height_std': float(np.std(eyebrow_positions)),
                'baseline_mouth_curvature': float(np.mean(mouth_positions)),
                'mouth_curvature_std': float(np.std(mouth_positions)),
                'expression_stability': float(1.0 / (np.std(eyebrow_positions) + np.std(mouth_positions) + 0.001))
            }
            
        except Exception as e:
            self.logger.error(f"Expression baseline analysis error: {e}")
            return {'error': str(e)}
    
    def _calculate_eyebrow_height(self, landmarks: List[Dict]) -> float:
        """Calculate relative eyebrow height as expression indicator."""
        try:
            # Get eyebrow and eye reference points
            left_eyebrow_idx = self.FACIAL_LANDMARKS['left_eyebrow']
            right_eyebrow_idx = self.FACIAL_LANDMARKS['right_eyebrow']
            left_eye_idx = self.FACIAL_LANDMARKS['left_eye_key']
            
            # Calculate average eyebrow position
            eyebrow_y = 0
            eye_y = 0
            count = 0
            
            for idx in left_eyebrow_idx + right_eyebrow_idx:
                if idx < len(landmarks):
                    eyebrow_y += landmarks[idx]['y']
                    count += 1
            
            for idx in left_eye_idx:
                if idx < len(landmarks):
                    eye_y += landmarks[idx]['y']
            
            if count == 0:
                return 0.0
            
            eyebrow_y /= count
            eye_y /= len(left_eye_idx)
            
            # Return relative position (negative = eyebrows raised)
            return float(eyebrow_y - eye_y)
            
        except Exception:
            return 0.0
    
    def _calculate_mouth_curvature(self, landmarks: List[Dict]) -> float:
        """Calculate mouth curvature as expression indicator."""
        try:
            mouth_idx = self.FACIAL_LANDMARKS['mouth_outer']
            
            if len(mouth_idx) < 6 or len(landmarks) <= max(mouth_idx):
                return 0.0
            
            # Get mouth corner and center points
            left_corner = landmarks[mouth_idx[0]]  # Left corner
            right_corner = landmarks[mouth_idx[6]]  # Right corner  
            center_top = landmarks[mouth_idx[3]]  # Top center
            center_bottom = landmarks[mouth_idx[9]]  # Bottom center
            
            # Calculate mouth curvature (positive = smile, negative = frown)
            corner_height = (left_corner['y'] + right_corner['y']) / 2
            mouth_center = (center_top['y'] + center_bottom['y']) / 2
            
            return float(corner_height - mouth_center)
            
        except Exception:
            return 0.0
    
    def _analyze_face_stability(self, landmarks_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze face position stability during baseline capture.
        
        Args:
            landmarks_data (List): Frame-by-frame landmark data
            
        Returns:
            Dict with face stability metrics
        """
        try:
            face_centers = []
            face_sizes = []
            
            for frame_data in landmarks_data:
                if not frame_data['face_detected']:
                    continue
                
                landmarks = frame_data['landmarks']
                if len(landmarks) < 100:  # Need sufficient landmarks
                    continue
                
                # Calculate face center
                x_coords = [l['x'] for l in landmarks]
                y_coords = [l['y'] for l in landmarks]
                
                face_center = (np.mean(x_coords), np.mean(y_coords))
                face_centers.append(face_center)
                
                # Calculate face size (bounding box area)
                face_width = max(x_coords) - min(x_coords)
                face_height = max(y_coords) - min(y_coords)
                face_sizes.append(face_width * face_height)
            
            if len(face_centers) < 10:
                return {'error': 'Insufficient face tracking data'}
            
            # Calculate stability metrics
            center_x_std = np.std([c[0] for c in face_centers])
            center_y_std = np.std([c[1] for c in face_centers])
            size_std = np.std(face_sizes)
            
            return {
                'position_stability_x': float(1.0 / (center_x_std + 1.0)),
                'position_stability_y': float(1.0 / (center_y_std + 1.0)),
                'size_stability': float(1.0 / (size_std + 1.0)),
                'overall_stability': float(1.0 / (center_x_std + center_y_std + size_std + 1.0))
            }
            
        except Exception as e:
            self.logger.error(f"Face stability analysis error: {e}")
            return {'error': str(e)}
    
    def analyze_speech_baseline(self, audio_path: str, duration_seconds: float = 15) -> Dict[str, Any]:
        """
        Analyze speech baseline audio to extract vocal behavior metrics.
        
        Args:
            audio_path (str): Path to baseline speech audio
            duration_seconds (float): Expected duration of baseline
            
        Returns:
            Dict with speech baseline metrics
        """
        try:
            self.logger.info(f"Analyzing speech baseline: {audio_path}")
            
            # For now, provide structure for speech analysis
            # Real implementation would use audio processing libraries
            speech_metrics = {
                'audio_path': audio_path,
                'duration_seconds': duration_seconds,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Placeholder for actual audio analysis
            # TODO: Implement with librosa or similar audio processing library
            pitch_metrics = self._analyze_pitch_baseline(audio_path)
            tone_metrics = self._analyze_tone_baseline(audio_path) 
            rate_metrics = self._analyze_speaking_rate_baseline(audio_path)
            quality_metrics = self._analyze_audio_quality_baseline(audio_path)
            
            speech_metrics.update({
                'pitch_baseline': pitch_metrics,
                'tone_baseline': tone_metrics,
                'rate_baseline': rate_metrics,
                'quality_baseline': quality_metrics
            })
            
            self.logger.info("Speech baseline analysis complete")
            return speech_metrics
            
        except Exception as e:
            self.logger.error(f"Speech baseline analysis error: {e}")
            return {
                'error': str(e),
                'audio_path': audio_path,
                'analysis_failed': True
            }
    
    def _analyze_pitch_baseline(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze baseline pitch and tone characteristics.
        
        Note: This is a placeholder implementation. Real implementation
        would use audio processing libraries like librosa.
        """
        return {
            'baseline_pitch_hz': 150.0,  # Placeholder values
            'pitch_range_hz': 50.0,
            'pitch_stability': 0.8,
            'analysis_method': 'placeholder'
        }
    
    def _analyze_tone_baseline(self, audio_path: str) -> Dict[str, Any]:
        """Analyze baseline tone and emotional characteristics."""
        return {
            'baseline_tone_energy': 0.6,
            'tone_warmth': 0.7,
            'tone_stability': 0.8,
            'analysis_method': 'placeholder'
        }
    
    def _analyze_speaking_rate_baseline(self, audio_path: str) -> Dict[str, Any]:
        """Analyze baseline speaking rate and rhythm."""
        return {
            'baseline_words_per_minute': 120.0,
            'pause_frequency': 0.3,
            'rhythm_regularity': 0.7,
            'analysis_method': 'placeholder'
        }
    
    def _analyze_audio_quality_baseline(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio quality metrics for baseline."""
        return {
            'baseline_snr_db': 22.0,
            'audio_clarity': 0.8,
            'background_noise_level': 0.1,
            'analysis_method': 'placeholder'
        }
    
    def _fallback_face_analysis(self, video_path: str, duration_seconds: float) -> Dict[str, Any]:
        """Fallback face analysis when MediaPipe is not available."""
        self.logger.warning("Using fallback face analysis - limited functionality")
        
        return {
            'video_path': video_path,
            'duration_seconds': duration_seconds,
            'analysis_method': 'fallback',
            'eye_baseline': {
                'baseline_eye_openness': 0.3,  # Default neutral values
                'baseline_blink_rate': 15.0,
            },
            'expression_baseline': {
                'baseline_eyebrow_height': 0.0,
                'baseline_mouth_curvature': 0.0,
            },
            'stability_metrics': {
                'overall_stability': 0.5,
            }
        }
    
    def compile_baseline_metrics(self, face_data: Dict[str, Any], speech_data: Dict[str, Any]) -> BaselineMetrics:
        """
        Compile face and speech data into comprehensive baseline metrics.
        
        Args:
            face_data (Dict): Face baseline analysis results
            speech_data (Dict): Speech baseline analysis results
            
        Returns:
            BaselineMetrics with compiled results
        """
        try:
            # Calculate overall quality score
            face_quality = self._calculate_face_quality_score(face_data)
            speech_quality = self._calculate_speech_quality_score(speech_data)
            overall_quality = (face_quality + speech_quality) / 2.0
            
            # Generate statistical summary
            stats = self._generate_statistical_summary(face_data, speech_data)
            
            baseline_metrics = BaselineMetrics(
                face_metrics=face_data,
                speech_metrics=speech_data,
                overall_quality={
                    'face_quality': face_quality,
                    'speech_quality': speech_quality,
                    'overall_quality': overall_quality,
                    'quality_rating': self._quality_rating(overall_quality)
                },
                statistical_summary=stats,
                created_at=datetime.now().isoformat(),
                session_id=self.session_id
            )
            
            self.logger.info(f"Baseline metrics compiled successfully: {overall_quality:.2f} quality")
            return baseline_metrics
            
        except Exception as e:
            self.logger.error(f"Error compiling baseline metrics: {e}")
            raise
    
    def _calculate_face_quality_score(self, face_data: Dict[str, Any]) -> float:
        """Calculate quality score for face baseline data."""
        if 'error' in face_data or face_data.get('analysis_failed'):
            return 0.0
        
        # Factors affecting face quality
        detection_rate = face_data.get('face_detection_rate', 0.0)
        stability = face_data.get('stability_metrics', {}).get('overall_stability', 0.5)
        
        # Weighted quality score
        quality = (detection_rate * 0.6 + stability * 0.4)
        return min(1.0, max(0.0, quality))
    
    def _calculate_speech_quality_score(self, speech_data: Dict[str, Any]) -> float:
        """Calculate quality score for speech baseline data."""
        if 'error' in speech_data or speech_data.get('analysis_failed'):
            return 0.0
        
        # Placeholder quality calculation
        # Real implementation would consider SNR, clarity, etc.
        return 0.8  # Default good quality
    
    def _generate_statistical_summary(self, face_data: Dict[str, Any], speech_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistical summary of baseline data."""
        return {
            'face_data_points': face_data.get('total_frames', 0),
            'speech_duration': speech_data.get('duration_seconds', 0),
            'analysis_timestamp': datetime.now().isoformat(),
            'data_completeness': {
                'face_complete': 'error' not in face_data,
                'speech_complete': 'error' not in speech_data,
                'overall_complete': 'error' not in face_data and 'error' not in speech_data
            }
        }
    
    def _quality_rating(self, quality_score: float) -> str:
        """Convert quality score to readable rating."""
        if quality_score >= 0.8:
            return "excellent"
        elif quality_score >= 0.6:
            return "good"
        elif quality_score >= 0.4:
            return "fair"
        else:
            return "poor"