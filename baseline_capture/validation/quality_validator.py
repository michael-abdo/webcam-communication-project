#!/usr/bin/env python3
"""
Quality Validator for Baseline Capture

Validates baseline capture quality according to SOP requirements:
- Face detection confidence >0.8 for at least 8 of 10 seconds
- Audio SNR >20dB for at least 10 seconds
- Real-time quality feedback during capture

Author: Baseline Capture System
Version: 1.0
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class ValidationResult:
    """Result of quality validation check"""
    is_valid: bool
    confidence_score: float
    snr_db: float
    validation_message: str
    timestamp: float


class QualityValidator:
    """
    Validates baseline capture quality for face and audio data.
    
    Uses existing MediaPipe integration for face detection and implements
    audio SNR calculation for real-time quality monitoring.
    """
    
    def __init__(self):
        """Initialize quality validator with MediaPipe and audio processing."""
        # SOP requirements from document
        self.FACE_CONFIDENCE_THRESHOLD = 0.8
        self.AUDIO_SNR_THRESHOLD_DB = 20.0
        self.MIN_VALID_SECONDS_FACE = 8  # out of 10 seconds
        self.MIN_VALID_SECONDS_AUDIO = 10  # out of 15 seconds
        
        # Initialize MediaPipe Face Mesh (reusing existing configuration)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,  # Lower than validation threshold for detection
            min_tracking_confidence=0.5
        )
        
        # Quality tracking
        self.face_quality_history = []
        self.audio_quality_history = []
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def validate_face_quality(self, frame: np.ndarray) -> ValidationResult:
        """
        Validate face detection quality for a single frame.
        
        Args:
            frame (np.ndarray): Video frame from webcam
            
        Returns:
            ValidationResult with face confidence score
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                # Face detected - calculate confidence based on landmark stability
                face_landmarks = results.multi_face_landmarks[0]
                
                # Use landmark count and distribution as confidence proxy
                # MediaPipe doesn't provide direct confidence, so we estimate it
                landmark_count = len(face_landmarks.landmark)
                
                # Expected landmark count is 468 for Face Mesh
                confidence = min(1.0, landmark_count / 468.0)
                
                # Additional confidence factors:
                # 1. Check if key facial features are detected (eyes, nose, mouth)
                if self._has_key_facial_features(face_landmarks, frame.shape):
                    confidence = min(1.0, confidence + 0.1)
                
                # 2. Check landmark stability (not implemented for single frame)
                # This would require multiple frames for proper implementation
                
                is_valid = confidence >= self.FACE_CONFIDENCE_THRESHOLD
                message = f"Face confidence: {confidence:.2f}"
                
            else:
                # No face detected
                confidence = 0.0
                is_valid = False
                message = "No face detected"
            
            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence,
                snr_db=0.0,  # Not applicable for face validation
                validation_message=message,
                timestamp=time.time()
            )
            
            # Store for batch validation
            self.face_quality_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Face validation error: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                snr_db=0.0,
                validation_message=f"Validation error: {e}",
                timestamp=time.time()
            )
    
    def validate_audio_quality(self, audio_data: np.ndarray, sample_rate: int = 44100) -> ValidationResult:
        """
        Validate audio signal-to-noise ratio for a chunk of audio data.
        
        Args:
            audio_data (np.ndarray): Audio samples
            sample_rate (int): Audio sample rate in Hz
            
        Returns:
            ValidationResult with SNR in dB
        """
        try:
            if len(audio_data) == 0:
                return ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    snr_db=0.0,
                    validation_message="No audio data",
                    timestamp=time.time()
                )
            
            # Calculate SNR using RMS energy method
            snr_db = self._calculate_audio_snr(audio_data)
            
            is_valid = snr_db >= self.AUDIO_SNR_THRESHOLD_DB
            message = f"Audio SNR: {snr_db:.1f} dB"
            
            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=0.0,  # Not applicable for audio validation
                snr_db=snr_db,
                validation_message=message,
                timestamp=time.time()
            )
            
            # Store for batch validation
            self.audio_quality_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Audio validation error: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                snr_db=0.0,
                validation_message=f"Audio validation error: {e}",
                timestamp=time.time()
            )
    
    def validate_baseline_batch(self, duration_seconds: float) -> Dict[str, Any]:
        """
        Validate complete baseline capture quality over time period.
        
        Args:
            duration_seconds (float): Expected capture duration
            
        Returns:
            Dict with overall validation results
        """
        # Validate face quality over time
        face_valid_count = sum(1 for r in self.face_quality_history if r.is_valid)
        face_total_count = len(self.face_quality_history)
        face_pass = face_valid_count >= self.MIN_VALID_SECONDS_FACE
        
        # Validate audio quality over time
        audio_valid_count = sum(1 for r in self.audio_quality_history if r.is_valid)
        audio_total_count = len(self.audio_quality_history)
        audio_pass = audio_valid_count >= self.MIN_VALID_SECONDS_AUDIO
        
        # Calculate average metrics
        avg_face_confidence = np.mean([r.confidence_score for r in self.face_quality_history]) if self.face_quality_history else 0.0
        avg_audio_snr = np.mean([r.snr_db for r in self.audio_quality_history]) if self.audio_quality_history else 0.0
        
        overall_pass = face_pass and audio_pass
        
        return {
            'overall_valid': overall_pass,
            'face_validation': {
                'passed': face_pass,
                'valid_seconds': face_valid_count,
                'total_seconds': face_total_count,
                'avg_confidence': avg_face_confidence,
                'threshold': self.FACE_CONFIDENCE_THRESHOLD
            },
            'audio_validation': {
                'passed': audio_pass,
                'valid_seconds': audio_valid_count,
                'total_seconds': audio_total_count,
                'avg_snr_db': avg_audio_snr,
                'threshold': self.AUDIO_SNR_THRESHOLD_DB
            },
            'recommendations': self._generate_recommendations(face_pass, audio_pass)
        }
    
    def _has_key_facial_features(self, face_landmarks, frame_shape: Tuple[int, int, int]) -> bool:
        """
        Check if key facial features (eyes, nose, mouth) are properly detected.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_shape: Frame dimensions
            
        Returns:
            bool: True if key features are detected
        """
        try:
            # MediaPipe Face Mesh landmark indices for key features
            LEFT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
            RIGHT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
            NOSE_TIP_INDICES = [1, 2, 5, 6, 19, 20, 94, 125, 141, 235, 236, 237, 238, 239, 240, 241, 242]
            MOUTH_INDICES = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
            
            h, w, _ = frame_shape
            
            # Check if landmarks exist for key features
            landmarks = face_landmarks.landmark
            
            # Verify eye regions have reasonable coordinates
            left_eye_points = [(landmarks[i].x * w, landmarks[i].y * h) for i in LEFT_EYE_INDICES if i < len(landmarks)]
            right_eye_points = [(landmarks[i].x * w, landmarks[i].y * h) for i in RIGHT_EYE_INDICES if i < len(landmarks)]
            nose_points = [(landmarks[i].x * w, landmarks[i].y * h) for i in NOSE_TIP_INDICES if i < len(landmarks)]
            mouth_points = [(landmarks[i].x * w, landmarks[i].y * h) for i in MOUTH_INDICES if i < len(landmarks)]
            
            # Basic sanity checks
            has_eyes = len(left_eye_points) > 8 and len(right_eye_points) > 8
            has_nose = len(nose_points) > 5
            has_mouth = len(mouth_points) > 6
            
            return has_eyes and has_nose and has_mouth
            
        except Exception:
            return False
    
    def _calculate_audio_snr(self, audio_data: np.ndarray) -> float:
        """
        Calculate Signal-to-Noise Ratio for audio data.
        
        Uses Voice Activity Detection approach:
        1. Detect speech vs silence segments
        2. Calculate RMS energy for speech (signal) and silence (noise)
        3. Return SNR in dB: 20 * log10(signal_rms / noise_rms)
        
        Args:
            audio_data (np.ndarray): Audio samples
            
        Returns:
            float: SNR in decibels
        """
        try:
            # Ensure audio is normalized
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            
            # Simple voice activity detection based on energy
            # More sophisticated VAD would use spectral features
            energy_threshold = np.percentile(np.abs(audio_data), 75)  # 75th percentile as threshold
            
            # Separate signal (high energy) and noise (low energy) segments
            high_energy_mask = np.abs(audio_data) > energy_threshold
            low_energy_mask = ~high_energy_mask
            
            if np.any(high_energy_mask) and np.any(low_energy_mask):
                # Calculate RMS for signal and noise segments
                signal_rms = np.sqrt(np.mean(audio_data[high_energy_mask] ** 2))
                noise_rms = np.sqrt(np.mean(audio_data[low_energy_mask] ** 2))
                
                # Avoid division by zero
                if noise_rms > 1e-10:
                    snr_db = 20 * np.log10(signal_rms / noise_rms)
                else:
                    snr_db = 60.0  # High SNR if no noise detected
            else:
                # Fallback: use overall RMS vs minimum detectable level
                if rms_energy > 1e-6:
                    snr_db = 20 * np.log10(rms_energy / 1e-6)  # Reference level
                else:
                    snr_db = 0.0
            
            # Clamp to reasonable range
            snr_db = max(0.0, min(60.0, snr_db))
            
            return snr_db
            
        except Exception as e:
            self.logger.error(f"SNR calculation error: {e}")
            return 0.0
    
    def _generate_recommendations(self, face_pass: bool, audio_pass: bool) -> List[str]:
        """
        Generate user recommendations based on validation results.
        
        Args:
            face_pass (bool): Whether face validation passed
            audio_pass (bool): Whether audio validation passed
            
        Returns:
            List[str]: Recommendation messages
        """
        recommendations = []
        
        if not face_pass:
            recommendations.extend([
                "Improve lighting - face your camera toward a light source",
                "Move closer to the camera (arm's length distance)",
                "Ensure your face is centered in the frame",
                "Remove any obstructions (glasses glare, hat, etc.)"
            ])
        
        if not audio_pass:
            recommendations.extend([
                "Move closer to your microphone",
                "Reduce background noise (close windows, turn off fans)",
                "Speak clearly and at normal volume",
                "Check microphone settings and permissions"
            ])
        
        if face_pass and audio_pass:
            recommendations.append("Baseline capture quality is excellent!")
        
        return recommendations
    
    def reset_history(self):
        """Reset quality history for new baseline capture session."""
        self.face_quality_history.clear()
        self.audio_quality_history.clear()
    
    def close(self):
        """Release MediaPipe resources."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()