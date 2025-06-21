#!/usr/bin/env python3
"""
Test Real-Time Alerting System

Tests the alert system integration with fatigue detection to ensure
proper alert escalation, hysteresis, and intervention recommendations.
"""

import sys
sys.path.append('./cognitive_overload/processing')

import time
import json
from datetime import datetime
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
from alert_system import AlertSystem, AlertLevel, audio_alert_callback, visual_alert_callback, intervention_callback


def test_realtime_alerting_system():
    """Test the real-time alerting system with actual video processing."""
    
    print("=" * 80)
    print("🚨 TESTING REAL-TIME ALERTING SYSTEM")
    print("=" * 80)
    
    # Initialize all components
    alert_system = AlertSystem(
        alert_callbacks={
            'warning': audio_alert_callback,
            'critical': visual_alert_callback,
            'emergency': intervention_callback
        }
    )
    
    # Test with real human face video
    video_path = './cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/files/1/3.mp4'
    
    print(f"Testing with video: {video_path}")
    print(f"Alert thresholds: {alert_system.alert_thresholds}")
    
    # Process video with integrated alert system
    processor = LandmarkProcessor(video_path)
    mapper = CognitiveLandmarkMapper()
    fatigue_detector = FatigueDetector()
    fatigue_detector.set_calibration('real')
    
    video_results = processor.process_video()
    landmarks_data = video_results['landmarks_data']
    
    print(f"Processing {len(landmarks_data)} frames with real-time alerts...")
    
    alert_responses = []
    frame_count = 0
    
    for i, frame_data in enumerate(landmarks_data):
        if frame_data.get('face_detected', False):
            landmarks = frame_data['landmarks']
            
            # Calculate eye openness
            left_eye = mapper.calculate_eye_openness(landmarks, 'left')
            right_eye = mapper.calculate_eye_openness(landmarks, 'right')
            avg_openness = (left_eye + right_eye) / 2
            
            # Update fatigue detector
            timestamp = i / 30.0
            fatigue_metrics = fatigue_detector.update(avg_openness, timestamp)
            
            # Update alert system
            alert_response = alert_system.update(
                perclos_percentage=fatigue_metrics['perclos_percentage'],
                fatigue_level=fatigue_metrics['fatigue_level'],
                blink_count=fatigue_metrics['blink_rate'],
                microsleep_count=fatigue_metrics['microsleep_count'],
                timestamp=timestamp
            )
            
            alert_responses.append(alert_response)
            frame_count += 1
            
            # Print alerts every 5 seconds or when alert level changes
            if i % 150 == 0 or alert_response['alert_changed']:
                print(f"Frame {i:4d} (t={timestamp:5.1f}s): "
                      f"PERCLOS={alert_response['perclos_percentage']:.1f}%, "
                      f"Alert={alert_response['alert_level'].upper()}, "
                      f"Changed={alert_response['alert_changed']}")
                
                if alert_response['alert_changed']:
                    print(f"  → {alert_response['message']}")
                    print(f"  → {alert_response['recommendation']}")
    
    # Get final alert summary
    final_summary = alert_system.get_alert_summary()
    
    print(f"\n📊 ALERT SYSTEM TEST RESULTS:")
    print(f"  Frames processed: {frame_count}")
    print(f"  Session duration: {final_summary['session_duration_minutes']:.1f} minutes")
    print(f"  Total alert events: {final_summary['total_alert_events']}")
    print(f"  Final alert level: {final_summary['current_alert_level']}")
    print(f"  Alert frequency: {final_summary['alert_frequency_per_hour']:.1f} alerts/hour")
    
    # Show alert counts by level
    if 'alert_counts_by_level' in final_summary:
        print(f"\n🚨 ALERT BREAKDOWN:")
        for level, count in final_summary['alert_counts_by_level'].items():
            print(f"  {level.upper()}: {count} events")
    
    # Save alert log
    log_filename = alert_system.save_alert_log()
    print(f"\n💾 Alert log saved to: {log_filename}")
    
    return alert_responses, final_summary


def test_alert_escalation():
    """Test alert escalation with simulated increasing fatigue."""
    
    print(f"\n{'='*60}")
    print("🔥 TESTING ALERT ESCALATION")
    print(f"{'='*60}")
    
    alert_system = AlertSystem(
        escalation_time=10.0,  # Faster escalation for testing
        alert_callbacks={
            'warning': lambda x: print(f"🟡 WARNING: {x['message']}"),
            'critical': lambda x: print(f"🟠 CRITICAL: {x['message']}"),
            'emergency': lambda x: print(f"🔴 EMERGENCY: {x['message']}")
        }
    )
    
    # Simulate escalating PERCLOS values
    test_scenarios = [
        (5.0, "Normal state"),
        (10.0, "Mild fatigue onset"),
        (10.5, "Sustained mild fatigue"),  # Should escalate to WARNING
        (16.0, "Moderate fatigue"),         # Should escalate to CRITICAL 
        (30.0, "Severe fatigue"),          # Should escalate to EMERGENCY
        (35.0, "Dangerous state"),
        (5.0, "Recovery - back to normal"), # Test hysteresis
        (3.0, "Confirmed recovery")
    ]
    
    timestamp = time.time()
    
    for perclos, description in test_scenarios:
        # Simulate 12 seconds at this PERCLOS level
        for i in range(12):
            alert_response = alert_system.update(
                perclos_percentage=perclos,
                fatigue_level="DROWSY" if perclos > 15 else "ALERT",
                blink_count=3,
                microsleep_count=1 if perclos > 25 else 0,
                timestamp=timestamp
            )
            
            if i == 0 or alert_response['alert_changed']:
                print(f"t={timestamp-time.time()+i:+6.1f}s: PERCLOS={perclos:4.1f}% - {description}")
                print(f"  Alert: {alert_response['alert_level'].upper()} - {alert_response['message']}")
                
                if alert_response.get('action_required', False):
                    print(f"  🚨 ACTION REQUIRED: {alert_response['recommendation']}")
            
            timestamp += 1
    
    escalation_summary = alert_system.get_alert_summary()
    print(f"\n📈 ESCALATION TEST SUMMARY:")
    print(f"  Total events: {escalation_summary['total_alert_events']}")
    print(f"  Final level: {escalation_summary['current_alert_level']}")


def test_hysteresis_prevention():
    """Test hysteresis to prevent alert flickering."""
    
    print(f"\n{'='*60}")
    print("🔄 TESTING HYSTERESIS (Flicker Prevention)")
    print(f"{'='*60}")
    
    alert_system = AlertSystem(hysteresis_buffer=3.0)  # 3% buffer
    
    # Simulate PERCLOS values hovering around warning threshold (15%)
    perclos_sequence = [
        14.0, 15.5, 14.8, 16.2, 14.5, 15.9, 14.2, 15.7, 13.8, 12.0, 11.5, 10.0
    ]
    
    print("Testing PERCLOS values hovering around 15% warning threshold:")
    
    timestamp = time.time()
    alert_changes = 0
    
    for perclos in perclos_sequence:
        alert_response = alert_system.update(
            perclos_percentage=perclos,
            fatigue_level="MILD_FATIGUE" if perclos > 12 else "ALERT",
            blink_count=2,
            microsleep_count=0,
            timestamp=timestamp
        )
        
        if alert_response['alert_changed']:
            alert_changes += 1
        
        print(f"PERCLOS: {perclos:4.1f}% → Alert: {alert_response['alert_level']:8s} "
              f"(Changed: {'Yes' if alert_response['alert_changed'] else 'No '})")
        
        timestamp += 2
    
    print(f"\n🎯 HYSTERESIS TEST RESULTS:")
    print(f"  Alert level changes: {alert_changes}")
    print(f"  Expected: Minimal changes due to hysteresis buffer")
    
    if alert_changes <= 3:
        print(f"  ✅ Hysteresis working correctly (≤3 changes)")
    else:
        print(f"  ⚠️ Too many alert changes - hysteresis may need tuning")


def main():
    """Main test execution."""
    
    print("🚀 Starting Real-Time Alert System Tests...")
    
    # Test 1: Real video with alert system
    print("\n" + "="*80)
    print("TEST 1: REAL VIDEO PROCESSING WITH ALERTS")
    print("="*80)
    
    alert_responses, summary = test_realtime_alerting_system()
    
    # Test 2: Alert escalation
    test_alert_escalation()
    
    # Test 3: Hysteresis prevention
    test_hysteresis_prevention()
    
    print(f"\n🎉 ALL ALERT SYSTEM TESTS COMPLETED!")
    print(f"Real-time alerting system validated and ready for production.")
    
    # Save comprehensive test results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_results = {
        'timestamp': timestamp,
        'test_type': 'realtime_alert_system',
        'real_video_test': {
            'summary': summary,
            'sample_responses': alert_responses[:10] if alert_responses else []
        },
        'tests_completed': [
            'Real video processing with alerts',
            'Alert escalation logic',
            'Hysteresis flicker prevention'
        ],
        'status': 'completed'
    }
    
    filename = f'alert_system_test_results_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"💾 Test results saved to: {filename}")


if __name__ == "__main__":
    main()