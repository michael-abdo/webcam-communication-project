#!/usr/bin/env python3
"""
Real-Time Alerting System for Fatigue Detection

Implements progressive fatigue alerts with hysteresis, audio/visual notifications,
and intervention recommendations based on validated PERCLOS thresholds.
"""

import time
import json
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Fatigue alert levels with progressive escalation."""
    ALERT = "alert"
    WARNING = "warning" 
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertSystem:
    """
    Real-time alerting system for fatigue detection with progressive escalation.
    
    Features:
    - Progressive alert levels based on PERCLOS thresholds
    - Hysteresis to prevent alert flickering
    - Audio and visual alert notifications
    - Intervention recommendations
    - Alert event logging for analysis
    """
    
    def __init__(self, 
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 hysteresis_buffer: float = 2.0,
                 escalation_time: float = 30.0,
                 alert_callbacks: Optional[Dict[str, Callable]] = None):
        """
        Initialize the alert system.
        
        Args:
            alert_thresholds: PERCLOS thresholds for each alert level
            hysteresis_buffer: Buffer percentage to prevent flickering (default 2%)
            escalation_time: Time in seconds before escalating to next level
            alert_callbacks: Optional callback functions for different alert types
        """
        
        # Default PERCLOS thresholds based on research and validation
        self.alert_thresholds = alert_thresholds or {
            AlertLevel.ALERT.value: 8.0,      # 8% PERCLOS = mild fatigue
            AlertLevel.WARNING.value: 15.0,    # 15% PERCLOS = moderate fatigue
            AlertLevel.CRITICAL.value: 25.0,   # 25% PERCLOS = severe fatigue
            AlertLevel.EMERGENCY.value: 40.0   # 40% PERCLOS = dangerous fatigue
        }
        
        self.hysteresis_buffer = hysteresis_buffer
        self.escalation_time = escalation_time
        
        # Current alert state
        self.current_alert_level = AlertLevel.ALERT
        self.last_alert_time = None
        self.alert_start_time = None
        self.consecutive_alerts = 0
        
        # Hysteresis tracking
        self.alert_history = deque(maxlen=30)  # Last 30 measurements for stability
        self.last_downgrade_time = None
        
        # Alert event logging
        self.alert_events = []
        self.session_start_time = datetime.now()
        
        # Callback functions for different alert types
        self.alert_callbacks = alert_callbacks or {}
        
        # Alert configuration
        self.audio_enabled = True
        self.visual_enabled = True
        self.intervention_enabled = True
        
        # Thread safety
        self.lock = threading.Lock()
    
    def update(self, perclos_percentage: float, 
               fatigue_level: str, 
               blink_count: int,
               microsleep_count: int,
               timestamp: Optional[float] = None) -> Dict[str, any]:
        """
        Update alert system with new fatigue metrics.
        
        Args:
            perclos_percentage: Current PERCLOS percentage
            fatigue_level: Current fatigue level from detector
            blink_count: Number of blinks detected
            microsleep_count: Number of microsleeps detected
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            Dictionary with alert status and recommendations
        """
        
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            # Determine alert level based on PERCLOS
            new_alert_level = self._determine_alert_level(perclos_percentage)
            
            # Apply hysteresis to prevent flickering
            stable_alert_level = self._apply_hysteresis(new_alert_level, perclos_percentage)
            
            # Check for alert escalation
            escalated_level = self._check_escalation(stable_alert_level, timestamp)
            
            # Update alert state
            alert_changed = self._update_alert_state(escalated_level, timestamp)
            
            # Generate alert response
            alert_response = self._generate_alert_response(
                escalated_level, perclos_percentage, fatigue_level,
                blink_count, microsleep_count, alert_changed, timestamp
            )
            
            # Log alert event if changed
            if alert_changed:
                self._log_alert_event(escalated_level, perclos_percentage, timestamp)
            
            # Trigger callbacks if registered
            if alert_changed and escalated_level.value in self.alert_callbacks:
                try:
                    self.alert_callbacks[escalated_level.value](alert_response)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
            
            return alert_response
    
    def _determine_alert_level(self, perclos_percentage: float) -> AlertLevel:
        """Determine alert level based on PERCLOS percentage."""
        
        if perclos_percentage >= self.alert_thresholds[AlertLevel.EMERGENCY.value]:
            return AlertLevel.EMERGENCY
        elif perclos_percentage >= self.alert_thresholds[AlertLevel.CRITICAL.value]:
            return AlertLevel.CRITICAL
        elif perclos_percentage >= self.alert_thresholds[AlertLevel.WARNING.value]:
            return AlertLevel.WARNING
        elif perclos_percentage >= self.alert_thresholds[AlertLevel.ALERT.value]:
            return AlertLevel.ALERT
        else:
            return AlertLevel.ALERT  # Below alert threshold = normal/alert state
    
    def _apply_hysteresis(self, new_level: AlertLevel, perclos: float) -> AlertLevel:
        """Apply hysteresis to prevent alert level flickering."""
        
        self.alert_history.append((perclos, new_level, time.time()))
        
        # If we're trying to downgrade alert level, apply hysteresis
        current_level_value = list(AlertLevel).index(self.current_alert_level)
        new_level_value = list(AlertLevel).index(new_level)
        
        if new_level_value < current_level_value:  # Downgrading
            # Require PERCLOS to be significantly below threshold for downgrade
            threshold = self.alert_thresholds[self.current_alert_level.value]
            buffer_threshold = threshold - self.hysteresis_buffer
            
            if perclos > buffer_threshold:
                # Still too close to threshold, maintain current level
                return self.current_alert_level
            
            # Check if we've been consistently below threshold
            if len(self.alert_history) >= 10:  # Need 10 consecutive measurements
                recent_perclos = [h[0] for h in list(self.alert_history)[-10:]]
                if all(p <= buffer_threshold for p in recent_perclos):
                    # Consistently below threshold, allow downgrade
                    self.last_downgrade_time = time.time()
                    return new_level
                else:
                    return self.current_alert_level
        
        return new_level
    
    def _check_escalation(self, alert_level: AlertLevel, timestamp: float) -> AlertLevel:
        """Check if alert should be escalated due to prolonged fatigue."""
        
        # If we're already at the same level for escalation_time, consider escalating
        if (alert_level == self.current_alert_level and 
            alert_level != AlertLevel.EMERGENCY and  # Can't escalate beyond emergency
            self.alert_start_time is not None):
            
            time_at_level = timestamp - self.alert_start_time
            
            if time_at_level >= self.escalation_time:
                # Escalate to next level
                current_index = list(AlertLevel).index(alert_level)
                if current_index < len(AlertLevel) - 1:
                    escalated_level = list(AlertLevel)[current_index + 1]
                    logger.info(f"Escalating alert: {alert_level.value} → {escalated_level.value} "
                               f"(sustained for {time_at_level:.1f}s)")
                    return escalated_level
        
        return alert_level
    
    def _update_alert_state(self, new_level: AlertLevel, timestamp: float) -> bool:
        """Update internal alert state and return True if alert level changed."""
        
        alert_changed = (new_level != self.current_alert_level)
        
        if alert_changed:
            self.current_alert_level = new_level
            self.alert_start_time = timestamp
            self.consecutive_alerts += 1
        
        self.last_alert_time = timestamp
        return alert_changed
    
    def _generate_alert_response(self, alert_level: AlertLevel, 
                               perclos: float, fatigue_level: str,
                               blink_count: int, microsleep_count: int,
                               alert_changed: bool, timestamp: float) -> Dict[str, any]:
        """Generate comprehensive alert response with recommendations."""
        
        # Base alert information
        alert_response = {
            'alert_level': alert_level.value,
            'alert_changed': alert_changed,
            'perclos_percentage': perclos,
            'fatigue_level': fatigue_level,
            'blink_count': blink_count,
            'microsleep_count': microsleep_count,
            'timestamp': timestamp,
            'session_duration': timestamp - time.mktime(self.session_start_time.timetuple())
        }
        
        # Add alert-specific information
        if alert_level == AlertLevel.ALERT:
            alert_response.update({
                'severity': 'normal',
                'message': 'Normal alertness level',
                'recommendation': 'Continue monitoring',
                'action_required': False,
                'audio_alert': False,
                'visual_alert': 'green'
            })
        
        elif alert_level == AlertLevel.WARNING:
            alert_response.update({
                'severity': 'mild',
                'message': 'Mild fatigue detected',
                'recommendation': 'Consider taking a break soon',
                'action_required': False,
                'audio_alert': self.audio_enabled,
                'visual_alert': 'yellow',
                'break_suggestion': 'Take a 5-10 minute break within next 15 minutes'
            })
        
        elif alert_level == AlertLevel.CRITICAL:
            alert_response.update({
                'severity': 'moderate',
                'message': 'Moderate fatigue detected - immediate attention needed',
                'recommendation': 'Take a break immediately',
                'action_required': True,
                'audio_alert': self.audio_enabled,
                'visual_alert': 'orange',
                'break_suggestion': 'Stop current activity and take 15-20 minute break now',
                'safety_concern': True
            })
        
        elif alert_level == AlertLevel.EMERGENCY:
            alert_response.update({
                'severity': 'severe',
                'message': 'SEVERE FATIGUE - STOP ACTIVITY IMMEDIATELY',
                'recommendation': 'STOP ALL ACTIVITIES - HIGH RISK DETECTED',
                'action_required': True,
                'audio_alert': True,  # Always play audio for emergency
                'visual_alert': 'red',
                'break_suggestion': 'STOP IMMEDIATELY - Get at least 30 minutes rest',
                'safety_concern': True,
                'emergency_alert': True
            })
        
        # Add intervention recommendations if enabled
        if self.intervention_enabled:
            alert_response['interventions'] = self._get_intervention_recommendations(
                alert_level, perclos, microsleep_count
            )
        
        # Add time-based information
        if self.alert_start_time:
            time_at_level = timestamp - self.alert_start_time
            alert_response['time_at_level'] = time_at_level
            
            if time_at_level > 60:  # More than 1 minute at this level
                alert_response['prolonged_fatigue'] = True
        
        return alert_response
    
    def _get_intervention_recommendations(self, alert_level: AlertLevel, 
                                        perclos: float, microsleep_count: int) -> List[str]:
        """Get specific intervention recommendations based on fatigue indicators."""
        
        interventions = []
        
        if alert_level == AlertLevel.WARNING:
            interventions.extend([
                "Increase lighting in workspace",
                "Take deep breaths and stretch",
                "Drink water or caffeine",
                "Check posture and adjust seating"
            ])
        
        elif alert_level == AlertLevel.CRITICAL:
            interventions.extend([
                "Stop current activity immediately",
                "Move to a comfortable rest area",
                "Close eyes for 10-15 minutes",
                "Inform supervisor/colleague of fatigue state"
            ])
            
            if microsleep_count > 0:
                interventions.append("Microsleeps detected - risk of falling asleep")
        
        elif alert_level == AlertLevel.EMERGENCY:
            interventions.extend([
                "EMERGENCY: Stop all activities now",
                "Find safe place to rest immediately",
                "Do not operate vehicles or machinery",
                "Contact someone for assistance if needed",
                "Consider medical attention if fatigue persists"
            ])
        
        return interventions
    
    def _log_alert_event(self, alert_level: AlertLevel, perclos: float, timestamp: float):
        """Log alert event for analysis and reporting."""
        
        event = {
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat(),
            'alert_level': alert_level.value,
            'perclos_percentage': perclos,
            'consecutive_alert_count': self.consecutive_alerts,
            'session_duration': timestamp - time.mktime(self.session_start_time.timetuple())
        }
        
        self.alert_events.append(event)
        
        # Keep only last 100 events to prevent memory issues
        if len(self.alert_events) > 100:
            self.alert_events = self.alert_events[-100:]
    
    def get_alert_summary(self) -> Dict[str, any]:
        """Get summary of alert events for the current session."""
        
        session_duration = time.time() - time.mktime(self.session_start_time.timetuple())
        
        if not self.alert_events:
            return {
                'status': 'No alerts generated this session',
                'session_duration_minutes': session_duration / 60,
                'total_alert_events': 0,
                'alert_frequency_per_hour': 0.0,
                'current_alert_level': self.current_alert_level.value,
                'last_alert_time': self.last_alert_time
            }
        
        # Calculate alert statistics
        alert_counts = {}
        for level in AlertLevel:
            alert_counts[level.value] = sum(1 for event in self.alert_events 
                                          if event['alert_level'] == level.value)
        
        total_alerts = len(self.alert_events)
        
        return {
            'session_duration_minutes': session_duration / 60,
            'total_alert_events': total_alerts,
            'alert_frequency_per_hour': (total_alerts / session_duration) * 3600 if session_duration > 0 else 0,
            'alert_counts_by_level': alert_counts,
            'current_alert_level': self.current_alert_level.value,
            'last_alert_time': self.last_alert_time,
            'recent_events': self.alert_events[-10:] if len(self.alert_events) > 10 else self.alert_events
        }
    
    def save_alert_log(self, filename: Optional[str] = None) -> str:
        """Save alert events to JSON file for analysis."""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'alert_log_{timestamp}.json'
        
        log_data = {
            'session_info': {
                'start_time': self.session_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (time.time() - time.mktime(self.session_start_time.timetuple())) / 60
            },
            'alert_configuration': {
                'thresholds': self.alert_thresholds,
                'hysteresis_buffer': self.hysteresis_buffer,
                'escalation_time': self.escalation_time
            },
            'session_summary': self.get_alert_summary(),
            'alert_events': self.alert_events
        }
        
        with open(filename, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        return filename
    
    def reset_session(self):
        """Reset alert system for new monitoring session."""
        
        with self.lock:
            self.current_alert_level = AlertLevel.ALERT
            self.last_alert_time = None
            self.alert_start_time = None
            self.consecutive_alerts = 0
            self.alert_history.clear()
            self.alert_events = []
            self.session_start_time = datetime.now()


# Example callback functions for different alert types
def audio_alert_callback(alert_response: Dict[str, any]):
    """Example audio alert callback function."""
    if alert_response.get('audio_alert', False):
        alert_level = alert_response['alert_level']
        # In real implementation, would play actual audio file


def visual_alert_callback(alert_response: Dict[str, any]):
    """Example visual alert callback function."""
    color = alert_response.get('visual_alert', 'green')
    message = alert_response['message']
    # In real implementation, would update UI elements


def intervention_callback(alert_response: Dict[str, any]):
    """Example intervention callback function."""
    if alert_response.get('action_required', False):
        # In real implementation, would trigger intervention actions
        pass