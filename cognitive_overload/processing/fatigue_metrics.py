#!/usr/bin/env python3
"""
Fatigue Detection Metrics Module

Implements research-validated fatigue detection algorithms including:
- PERCLOS (Percentage of Eyelid Closure) - industry standard
- Blink rate and duration analysis
- Microsleep detection
- Temporal analysis over sliding windows

Based on proven research with established thresholds.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import deque
from datetime import datetime, timedelta
import time


class FatigueDetector:
    """
    Detects fatigue using validated metrics from drowsiness research.
    
    Key metrics:
    - PERCLOS: % of time eyes are 80% closed over 1 minute
    - Blink rate: Normal is 15-20 blinks/minute
    - Microsleeps: Eye closures lasting >500ms
    """
    
    def __init__(self, 
                 perclos_threshold: float = 0.15,  # 15% = drowsy (validated)
                 eye_closed_threshold: float = 0.2,  # 80% closed
                 window_duration: int = 60,  # 1 minute window
                 fps: int = 30):  # Expected frame rate
        """
        Initialize fatigue detector with research-validated thresholds.
        
        Args:
            perclos_threshold: PERCLOS > this value indicates drowsiness
            eye_closed_threshold: Eye openness < this = closed
            window_duration: Sliding window duration in seconds
            fps: Expected frames per second for temporal analysis
        """
        self.perclos_threshold = perclos_threshold
        self.eye_closed_threshold = eye_closed_threshold
        self.window_duration = window_duration
        self.fps = fps
        
        # Sliding window for temporal analysis
        self.window_size = window_duration * fps
        self.eye_states = deque(maxlen=self.window_size)
        self.timestamps = deque(maxlen=self.window_size)
        
        # Blink detection state
        self.last_eye_state = 'open'
        self.blink_start_time = None
        self.blinks = []  # List of (timestamp, duration) tuples
        
        # Calibration for real vs synthetic faces
        self.calibration_mode = 'real'  # 'real' or 'synthetic'
        
    def set_calibration(self, mode: str = 'real'):
        """
        Set calibration mode for different face types.
        
        Args:
            mode: 'real' for human faces, 'synthetic' for artificial faces
        """
        self.calibration_mode = mode
        if mode == 'synthetic':
            # Synthetic faces have higher eye openness values (0.18-0.22)
            # Set threshold at ~80% of their range
            self.eye_closed_threshold = 0.15  # Adjusted for synthetic
        else:
            # Real faces have lower eye openness values (0.09-0.11)
            # Set threshold at ~80% of their range  
            self.eye_closed_threshold = 0.08  # Adjusted for real faces
    
    def update(self, eye_openness: float, timestamp: Optional[float] = None) -> Dict[str, any]:
        """
        Update fatigue metrics with new eye openness measurement.
        
        Args:
            eye_openness: Current eye openness ratio (0-1)
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            Dictionary with current fatigue metrics
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Determine if eyes are closed
        eyes_closed = eye_openness < self.eye_closed_threshold
        
        # Update sliding window
        self.eye_states.append(eyes_closed)
        self.timestamps.append(timestamp)
        
        # Detect blinks and microsleeps
        self._detect_blinks(eyes_closed, timestamp)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        return metrics
    
    def _detect_blinks(self, eyes_closed: bool, timestamp: float):
        """Detect blinks and microsleeps based on eye state transitions."""
        current_state = 'closed' if eyes_closed else 'open'
        
        if self.last_eye_state == 'open' and current_state == 'closed':
            # Start of blink
            self.blink_start_time = timestamp
            
        elif self.last_eye_state == 'closed' and current_state == 'open':
            # End of blink
            if self.blink_start_time is not None:
                blink_duration = (timestamp - self.blink_start_time) * 1000  # ms
                self.blinks.append((timestamp, blink_duration))
                
                # Keep only blinks from last window_duration seconds
                cutoff_time = timestamp - self.window_duration
                self.blinks = [(t, d) for t, d in self.blinks if t > cutoff_time]
        
        self.last_eye_state = current_state
    
    def _calculate_metrics(self) -> Dict[str, any]:
        """Calculate all fatigue metrics from current window."""
        metrics = {}
        
        # PERCLOS calculation
        if len(self.eye_states) > 0:
            perclos = sum(self.eye_states) / len(self.eye_states)
        else:
            perclos = 0.0
        
        metrics['perclos'] = perclos
        metrics['perclos_percentage'] = perclos * 100
        
        # Fatigue level classification
        if perclos < 0.08:
            fatigue_level = 'ALERT'
        elif perclos < self.perclos_threshold:
            fatigue_level = 'MILD_FATIGUE'
        elif perclos < 0.25:
            fatigue_level = 'DROWSY'
        else:
            fatigue_level = 'SEVERE_FATIGUE'
        
        metrics['fatigue_level'] = fatigue_level
        
        # Blink rate (per minute)
        current_time = self.timestamps[-1] if self.timestamps else time.time()
        recent_blinks = [d for t, d in self.blinks 
                        if current_time - t <= 60]  # Last minute
        
        metrics['blink_rate'] = len(recent_blinks)
        
        # Microsleep detection (blinks > 500ms)
        microsleeps = [d for t, d in self.blinks if d > 500]
        metrics['microsleep_count'] = len(microsleeps)
        
        # Average blink duration
        if recent_blinks:
            metrics['avg_blink_duration_ms'] = np.mean(recent_blinks)
        else:
            metrics['avg_blink_duration_ms'] = 0
        
        # Recommendations based on fatigue level
        if fatigue_level == 'ALERT':
            recommendation = 'Continue monitoring'
        elif fatigue_level == 'MILD_FATIGUE':
            recommendation = 'Consider taking a break soon'
        elif fatigue_level == 'DROWSY':
            recommendation = 'Take a break immediately'
        else:  # SEVERE_FATIGUE
            recommendation = 'Stop activity - high risk detected'
        
        metrics['recommendation'] = recommendation
        
        # Add temporal consistency
        metrics['data_points'] = len(self.eye_states)
        metrics['window_coverage'] = len(self.eye_states) / self.window_size
        
        return metrics
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of fatigue metrics over entire session."""
        if not self.eye_states:
            return {'status': 'No data collected'}
        
        total_closed = sum(self.eye_states)
        total_frames = len(self.eye_states)
        
        summary = {
            'session_duration_seconds': len(self.eye_states) / self.fps,
            'overall_perclos': (total_closed / total_frames) * 100,
            'total_blinks': len(self.blinks),
            'total_microsleeps': len([d for t, d in self.blinks if d > 500]),
            'calibration_mode': self.calibration_mode
        }
        
        # Add blink statistics
        if self.blinks:
            blink_durations = [d for t, d in self.blinks]
            summary['min_blink_duration_ms'] = min(blink_durations)
            summary['max_blink_duration_ms'] = max(blink_durations)
            summary['avg_blink_duration_ms'] = np.mean(blink_durations)
        
        return summary


class AttentionDetector:
    """
    Detects attention/focus using gaze patterns and stability.
    
    Metrics:
    - Gaze stability: How steady is the gaze direction
    - Focus duration: Time spent looking at specific regions
    - Distraction events: Rapid gaze shifts
    """
    
    def __init__(self, stability_threshold: float = 0.1, window_size: int = 30):
        """
        Initialize attention detector.
        
        Args:
            stability_threshold: Maximum gaze movement for "focused" state
            window_size: Number of frames for stability calculation
        """
        self.stability_threshold = stability_threshold
        self.window_size = window_size
        
        # Sliding window for gaze positions
        self.gaze_history = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        
        # Focus tracking
        self.focus_start_time = None
        self.focus_sessions = []  # List of (start, end, duration) tuples
        
    def update(self, gaze_position: Tuple[float, float], 
               timestamp: Optional[float] = None) -> Dict[str, any]:
        """
        Update attention metrics with new gaze position.
        
        Args:
            gaze_position: (x, y) normalized gaze coordinates
            timestamp: Optional timestamp
            
        Returns:
            Dictionary with attention metrics
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.gaze_history.append(gaze_position)
        self.timestamps.append(timestamp)
        
        metrics = self._calculate_metrics()
        
        # Track focus sessions
        self._track_focus(metrics['gaze_stability'], timestamp)
        
        return metrics
    
    def _calculate_metrics(self) -> Dict[str, any]:
        """Calculate attention metrics from gaze history."""
        if len(self.gaze_history) < 2:
            return {
                'gaze_stability': 1.0,
                'attention_state': 'UNKNOWN',
                'distraction_score': 0.0
            }
        
        # Calculate gaze stability (inverse of movement)
        positions = np.array(self.gaze_history)
        movements = np.diff(positions, axis=0)
        movement_magnitudes = np.sqrt(np.sum(movements**2, axis=1))
        
        avg_movement = np.mean(movement_magnitudes)
        gaze_stability = 1.0 - min(avg_movement / self.stability_threshold, 1.0)
        
        # Classify attention state
        if gaze_stability > 0.8:
            attention_state = 'FOCUSED'
        elif gaze_stability > 0.5:
            attention_state = 'MODERATE_FOCUS'
        else:
            attention_state = 'DISTRACTED'
        
        # Calculate distraction score (rapid movements)
        rapid_movements = movement_magnitudes > (2 * self.stability_threshold)
        distraction_score = np.sum(rapid_movements) / len(movement_magnitudes)
        
        return {
            'gaze_stability': gaze_stability,
            'attention_state': attention_state,
            'distraction_score': distraction_score,
            'avg_gaze_movement': avg_movement
        }
    
    def _track_focus(self, gaze_stability: float, timestamp: float):
        """Track continuous focus sessions."""
        is_focused = gaze_stability > 0.7
        
        if is_focused and self.focus_start_time is None:
            # Start of focus session
            self.focus_start_time = timestamp
            
        elif not is_focused and self.focus_start_time is not None:
            # End of focus session
            duration = timestamp - self.focus_start_time
            self.focus_sessions.append((self.focus_start_time, timestamp, duration))
            self.focus_start_time = None
            
            # Keep only recent sessions (last 5 minutes)
            cutoff_time = timestamp - 300
            self.focus_sessions = [(s, e, d) for s, e, d in self.focus_sessions 
                                  if e > cutoff_time]
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of attention metrics."""
        if not self.focus_sessions:
            return {'status': 'No focus sessions recorded'}
        
        durations = [d for s, e, d in self.focus_sessions]
        
        return {
            'total_focus_sessions': len(self.focus_sessions),
            'avg_focus_duration': np.mean(durations),
            'max_focus_duration': max(durations),
            'total_focus_time': sum(durations)
        }