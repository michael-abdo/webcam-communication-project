#!/usr/bin/env python3
"""
Baseline Capture Session Manager

Orchestrates the complete baseline capture process:
- 10-second neutral face baseline capture
- 15-second speech calibration capture  
- Real-time quality validation integration
- Retry logic and error handling
- Session state management

Author: Baseline Capture System
Version: 1.0
"""

import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Import our existing validation and storage modules
from baseline_capture.validation import QualityValidator
from baseline_capture.storage import BaselineStorage


class BaselineSessionState(Enum):
    """Baseline capture session states"""
    INITIALIZED = "initialized"
    FACE_CAPTURE = "face_capture"
    SPEECH_CAPTURE = "speech_capture"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CaptureResult:
    """Result of a baseline capture attempt"""
    success: bool
    session_id: str
    capture_type: str  # 'face' or 'speech'
    duration_seconds: float
    quality_score: float
    retry_needed: bool
    error_message: Optional[str] = None
    capture_data: Optional[Dict[str, Any]] = None


class BaselineCapture:
    """
    Main orchestrator for baseline capture sessions.
    
    Manages the complete baseline capture workflow:
    1. Session initialization
    2. Face baseline capture (10s)
    3. Speech baseline capture (15s)
    4. Quality validation and retry logic
    5. Data storage and finalization
    """
    
    def __init__(self, user_id: str = None, session_id: str = None):
        """
        Initialize baseline capture session.
        
        Args:
            user_id (str): Optional user identifier
            session_id (str): Optional existing session ID (for resume)
        """
        # Session management
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id or f"user_{int(time.time())}"
        self.state = BaselineSessionState.INITIALIZED
        self.created_at = datetime.now()
        
        # Capture tracking
        self.face_capture_attempts = []
        self.speech_capture_attempts = []
        self.current_attempt = None
        
        # Session configuration (from SOP document)
        self.config = {
            'face_duration_seconds': 10,
            'speech_duration_seconds': 15,
            'max_retry_attempts': 3,
            'face_confidence_threshold': 0.8,
            'audio_snr_threshold_db': 20.0,
            'min_valid_seconds_face': 8,  # out of 10
            'min_valid_seconds_speech': 10,  # out of 15
        }
        
        # Initialize validators and storage
        self.quality_validator = QualityValidator()
        self.baseline_storage = BaselineStorage()
        
        # Session data
        self.session_data = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'config': self.config,
            'face_attempts': [],
            'speech_attempts': [],
            'final_baseline_data': None
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Baseline capture session initialized: {self.session_id}")
    
    def start_session(self) -> Dict[str, Any]:
        """
        Start baseline capture session and prepare for face capture.
        
        Returns:
            Dict with session info and next steps
        """
        try:
            if self.state != BaselineSessionState.INITIALIZED:
                return {
                    'success': False,
                    'error': f'Session already started. Current state: {self.state.value}'
                }
            
            # Update state
            self.state = BaselineSessionState.FACE_CAPTURE
            self.session_data['state'] = self.state.value
            self.session_data['started_at'] = datetime.now().isoformat()
            
            # Generate S3 upload URLs for baseline media
            upload_urls = self.baseline_storage.generate_baseline_upload_urls(self.session_id)
            
            if 'error' in upload_urls:
                self.logger.error(f"Failed to generate upload URLs: {upload_urls['error']}")
                self.state = BaselineSessionState.FAILED
                return {
                    'success': False,
                    'error': 'Failed to prepare storage for baseline capture'
                }
            
            # Reset quality validator history
            self.quality_validator.reset_history()
            
            result = {
                'success': True,
                'session_id': self.session_id,
                'user_id': self.user_id,
                'state': self.state.value,
                'config': self.config,
                'upload_urls': upload_urls,
                'next_step': 'face_baseline',
                'instructions': {
                    'face_baseline': [
                        'Sit comfortably in front of your camera',
                        'Look directly at the camera with a neutral expression',
                        'Keep your eyes naturally open',
                        'Stay still for 10 seconds',
                        'Ensure good lighting on your face'
                    ]
                }
            }
            
            self.logger.info(f"Session started successfully: {self.session_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            self.state = BaselineSessionState.FAILED
            return {
                'success': False,
                'error': f'Failed to start session: {str(e)}'
            }
    
    def capture_face_baseline(self, video_path: str = None, duration: float = None) -> CaptureResult:
        """
        Orchestrate 10-second face baseline capture with quality validation.
        
        Args:
            video_path (str): Path to captured video file (optional for validation)
            duration (float): Actual capture duration
            
        Returns:
            CaptureResult with face baseline results
        """
        try:
            if self.state != BaselineSessionState.FACE_CAPTURE:
                return CaptureResult(
                    success=False,
                    session_id=self.session_id,
                    capture_type='face',
                    duration_seconds=0,
                    quality_score=0.0,
                    retry_needed=False,
                    error_message=f'Invalid state for face capture: {self.state.value}'
                )
            
            # Capture configuration
            target_duration = duration or self.config['face_duration_seconds']
            attempt_number = len(self.face_capture_attempts) + 1
            
            self.logger.info(f"Starting face baseline capture attempt {attempt_number}")
            
            # Create attempt record
            attempt_data = {
                'attempt_number': attempt_number,
                'started_at': datetime.now().isoformat(),
                'target_duration': target_duration,
                'capture_type': 'face'
            }
            
            # For now, simulate capture process
            # In real implementation, this would coordinate with frontend
            capture_start_time = time.time()
            
            # Simulate quality checking during capture
            # Real implementation would receive real-time frames
            quality_checks = []
            for second in range(int(target_duration)):
                # Simulate frame-by-frame quality check
                # Real implementation would process actual video frames
                simulated_quality = self._simulate_face_quality(second)
                quality_checks.append(simulated_quality)
                time.sleep(0.1)  # Brief pause for simulation
            
            actual_duration = time.time() - capture_start_time
            
            # Analyze overall quality
            valid_seconds = sum(1 for q in quality_checks if q.is_valid)
            average_confidence = sum(q.confidence_score for q in quality_checks) / len(quality_checks)
            
            # Determine if capture meets requirements
            quality_passed = valid_seconds >= self.config['min_valid_seconds_face']
            
            # Complete attempt record
            attempt_data.update({
                'completed_at': datetime.now().isoformat(),
                'actual_duration': actual_duration,
                'quality_checks': len(quality_checks),
                'valid_seconds': valid_seconds,
                'average_confidence': average_confidence,
                'quality_passed': quality_passed,
                'video_path': video_path
            })
            
            # Store attempt
            self.face_capture_attempts.append(attempt_data)
            self.session_data['face_attempts'] = self.face_capture_attempts
            
            # Create result
            result = CaptureResult(
                success=quality_passed,
                session_id=self.session_id,
                capture_type='face',
                duration_seconds=actual_duration,
                quality_score=average_confidence,
                retry_needed=not quality_passed and attempt_number < self.config['max_retry_attempts'],
                capture_data=attempt_data
            )
            
            if quality_passed:
                self.logger.info(f"Face baseline capture successful: {average_confidence:.2f} confidence")
                # Move to speech capture phase
                self.state = BaselineSessionState.SPEECH_CAPTURE
                self.session_data['state'] = self.state.value
            else:
                self.logger.warning(f"Face baseline quality insufficient: {valid_seconds}/{self.config['min_valid_seconds_face']} valid seconds")
                if not result.retry_needed:
                    self.state = BaselineSessionState.FAILED
                    result.error_message = "Maximum face capture attempts reached"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during face baseline capture: {e}")
            return CaptureResult(
                success=False,
                session_id=self.session_id,
                capture_type='face',
                duration_seconds=0,
                quality_score=0.0,
                retry_needed=False,
                error_message=f'Face capture error: {str(e)}'
            )
    
    def capture_speech_baseline(self, audio_path: str = None, duration: float = None) -> CaptureResult:
        """
        Orchestrate 15-second speech baseline capture with SNR validation.
        
        Args:
            audio_path (str): Path to captured audio file (optional for validation)
            duration (float): Actual capture duration
            
        Returns:
            CaptureResult with speech baseline results
        """
        try:
            if self.state != BaselineSessionState.SPEECH_CAPTURE:
                return CaptureResult(
                    success=False,
                    session_id=self.session_id,
                    capture_type='speech',
                    duration_seconds=0,
                    quality_score=0.0,
                    retry_needed=False,
                    error_message=f'Invalid state for speech capture: {self.state.value}'
                )
            
            # Capture configuration
            target_duration = duration or self.config['speech_duration_seconds']
            attempt_number = len(self.speech_capture_attempts) + 1
            
            self.logger.info(f"Starting speech baseline capture attempt {attempt_number}")
            
            # Create attempt record
            attempt_data = {
                'attempt_number': attempt_number,
                'started_at': datetime.now().isoformat(),
                'target_duration': target_duration,
                'capture_type': 'speech'
            }
            
            # For now, simulate capture process
            capture_start_time = time.time()
            
            # Simulate quality checking during capture
            quality_checks = []
            for second in range(int(target_duration)):
                # Simulate audio quality check
                simulated_quality = self._simulate_speech_quality(second)
                quality_checks.append(simulated_quality)
                time.sleep(0.1)  # Brief pause for simulation
            
            actual_duration = time.time() - capture_start_time
            
            # Analyze overall quality
            valid_seconds = sum(1 for q in quality_checks if q.is_valid)
            average_snr = sum(q.snr_db for q in quality_checks) / len(quality_checks)
            
            # Determine if capture meets requirements
            quality_passed = valid_seconds >= self.config['min_valid_seconds_speech']
            
            # Complete attempt record
            attempt_data.update({
                'completed_at': datetime.now().isoformat(),
                'actual_duration': actual_duration,
                'quality_checks': len(quality_checks),
                'valid_seconds': valid_seconds,
                'average_snr_db': average_snr,
                'quality_passed': quality_passed,
                'audio_path': audio_path
            })
            
            # Store attempt
            self.speech_capture_attempts.append(attempt_data)
            self.session_data['speech_attempts'] = self.speech_capture_attempts
            
            # Create result
            result = CaptureResult(
                success=quality_passed,
                session_id=self.session_id,
                capture_type='speech',
                duration_seconds=actual_duration,
                quality_score=average_snr,
                retry_needed=not quality_passed and attempt_number < self.config['max_retry_attempts'],
                capture_data=attempt_data
            )
            
            if quality_passed:
                self.logger.info(f"Speech baseline capture successful: {average_snr:.1f} dB SNR")
                # Move to processing phase
                self.state = BaselineSessionState.PROCESSING
                self.session_data['state'] = self.state.value
            else:
                self.logger.warning(f"Speech baseline quality insufficient: {valid_seconds}/{self.config['min_valid_seconds_speech']} valid seconds")
                if not result.retry_needed:
                    self.state = BaselineSessionState.FAILED
                    result.error_message = "Maximum speech capture attempts reached"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during speech baseline capture: {e}")
            return CaptureResult(
                success=False,
                session_id=self.session_id,
                capture_type='speech',
                duration_seconds=0,
                quality_score=0.0,
                retry_needed=False,
                error_message=f'Speech capture error: {str(e)}'
            )
    
    def _simulate_face_quality(self, second: int):
        """Simulate face quality validation for testing."""
        # Simulate improving quality over time
        base_confidence = 0.6 + (second * 0.03)  # Gradually improves
        confidence = min(1.0, base_confidence + (0.1 if second > 3 else 0))
        
        return type('QualityResult', (), {
            'is_valid': confidence >= self.config['face_confidence_threshold'],
            'confidence_score': confidence,
            'snr_db': 0.0,
            'timestamp': time.time()
        })()
    
    def _simulate_speech_quality(self, second: int):
        """Simulate speech quality validation for testing."""
        # Simulate variable audio quality
        base_snr = 18.0 + (second * 0.5)  # Gradually improves
        snr = min(30.0, base_snr + (3.0 if second > 5 else 0))
        
        return type('QualityResult', (), {
            'is_valid': snr >= self.config['audio_snr_threshold_db'],
            'confidence_score': 0.0,
            'snr_db': snr,
            'timestamp': time.time()
        })()
    
    def finalize_baseline(self) -> Dict[str, Any]:
        """
        Finalize baseline capture and compile results.
        
        Processes successful face and speech captures to create final
        baseline metrics for use in assessments.
        
        Returns:
            Dict with finalized baseline results
        """
        try:
            if self.state != BaselineSessionState.PROCESSING:
                return {
                    'success': False,
                    'error': f'Cannot finalize baseline. Current state: {self.state.value}'
                }
            
            # Check if we have successful captures
            successful_face = [a for a in self.face_capture_attempts if a.get('quality_passed', False)]
            successful_speech = [a for a in self.speech_capture_attempts if a.get('quality_passed', False)]
            
            if not successful_face and not successful_speech:
                return {
                    'success': False,
                    'error': 'No successful baseline captures to finalize'
                }
            
            # Get best quality attempts
            best_face = max(successful_face, key=lambda x: x.get('average_confidence', 0)) if successful_face else None
            best_speech = max(successful_speech, key=lambda x: x.get('average_snr_db', 0)) if successful_speech else None
            
            # Compile final baseline data
            final_baseline = {
                'session_id': self.session_id,
                'user_id': self.user_id,
                'finalized_at': datetime.now().isoformat(),
                'face_baseline': best_face,
                'speech_baseline': best_speech,
                'session_summary': {
                    'total_face_attempts': len(self.face_capture_attempts),
                    'total_speech_attempts': len(self.speech_capture_attempts),
                    'successful_face_attempts': len(successful_face),
                    'successful_speech_attempts': len(successful_speech),
                    'final_quality_score': self._calculate_overall_quality(best_face, best_speech)
                }
            }
            
            # Store final baseline data
            self.session_data['final_baseline_data'] = final_baseline
            
            # Update session state
            self.state = BaselineSessionState.COMPLETED
            self.session_data['state'] = self.state.value
            self.session_data['completed_at'] = datetime.now().isoformat()
            
            # Store baseline metrics
            storage_result = self.baseline_storage.store_baseline_metrics(
                self.session_id,
                final_baseline
            )
            
            if not storage_result:
                self.logger.warning(f"Failed to store baseline metrics for session: {self.session_id}")
            
            self.logger.info(f"Baseline finalized successfully: {final_baseline['session_summary']['final_quality_score']:.2f} quality")
            
            return {
                'success': True,
                'session_id': self.session_id,
                'final_baseline_data': final_baseline,
                'storage_successful': storage_result
            }
            
        except Exception as e:
            self.logger.error(f"Error finalizing baseline: {e}")
            self.state = BaselineSessionState.FAILED
            return {
                'success': False,
                'error': f'Finalization failed: {str(e)}'
            }
    
    def _calculate_overall_quality(self, face_data: Optional[Dict], speech_data: Optional[Dict]) -> float:
        """
        Calculate overall quality score for baseline capture.
        
        Args:
            face_data: Best face capture data
            speech_data: Best speech capture data
            
        Returns:
            float: Overall quality score (0-1)
        """
        try:
            face_quality = 0.0
            speech_quality = 0.0
            
            if face_data:
                face_quality = face_data.get('average_confidence', 0.0)
            
            if speech_data:
                # Convert SNR to 0-1 scale (assuming 20-30 dB is good range)
                snr = speech_data.get('average_snr_db', 0.0)
                speech_quality = min(1.0, max(0.0, (snr - 10.0) / 20.0))  # 10-30 dB -> 0-1
            
            # Weight face and speech equally if both present
            if face_data and speech_data:
                return (face_quality + speech_quality) / 2.0
            elif face_data:
                return face_quality
            elif speech_data:
                return speech_quality
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating overall quality: {e}")
            return 0.0

    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and progress.
        
        Returns:
            Dict with session state and progress information
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'state': self.state.value,
            'created_at': self.session_data['created_at'],
            'face_attempts': len(self.face_capture_attempts),
            'speech_attempts': len(self.speech_capture_attempts),
            'config': self.config,
            'progress': {
                'face_complete': len([a for a in self.face_capture_attempts if a.get('quality_passed', False)]) > 0,
                'speech_complete': len([a for a in self.speech_capture_attempts if a.get('quality_passed', False)]) > 0,
                'ready_for_processing': self.state == BaselineSessionState.PROCESSING
            }
        }
    
    def cleanup_session(self):
        """Clean up session resources."""
        try:
            if hasattr(self, 'quality_validator'):
                self.quality_validator.close()
            
            self.logger.info(f"Session cleanup completed: {self.session_id}")
            
        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup_session()