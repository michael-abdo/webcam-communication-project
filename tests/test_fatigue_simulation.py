#!/usr/bin/env python3
"""
Test Fatigue Analysis - Simulated Testing

Tests the fatigue detection algorithms without requiring MediaPipe
by simulating eye openness values.
"""

import sys
import time
import random
import numpy as np
from datetime import datetime

# Add paths
sys.path.append('./cognitive_overload/processing')
sys.path.append('./camera_tools')

# Import fatigue components (these don't require MediaPipe)
from fatigue_metrics import FatigueDetector
from alert_system import AlertSystem
from foundation_enforcer import requires, validator

# Import camera test
from tests.quick_camera_test import test_camera


class FatigueAnalysisTest:
    """Test fatigue analysis with simulated data."""
    
    def __init__(self):
        self.fatigue_detector = FatigueDetector()
        self.fatigue_detector.set_calibration('real')
        self.alert_system = AlertSystem()
        
        # Simulation parameters
        self.simulation_running = False
        self.start_time = None
        self.metrics_history = []
        self.alert_history = []
    
    @requires('foundation')
    def validate_camera(self):
        """Ensure camera is working (enforced)."""
        print("✅ Camera validated - foundation requirement met")
        return True
    
    def simulate_eye_openness(self, elapsed_time):
        """
        Simulate realistic eye openness values over time.
        Simulates gradual fatigue onset.
        """
        # Base alertness (decreases over time)
        base_alertness = 1.0 - (elapsed_time / 300)  # Decreases over 5 minutes
        base_alertness = max(0.3, base_alertness)  # Minimum 30% alertness
        
        # Add natural variation
        variation = random.gauss(0, 0.02)
        
        # Simulate blinks (quick closures)
        if random.random() < 0.05:  # 5% chance of blink
            return 0.05 + random.random() * 0.05
        
        # Simulate microsleeps (longer closures when tired)
        if base_alertness < 0.5 and random.random() < 0.02:
            return 0.02 + random.random() * 0.03
        
        # Normal eye openness
        openness = base_alertness * 0.15 + variation  # Scale to realistic range
        return max(0.02, min(0.20, openness))  # Clamp to realistic bounds
    
    def run_simulation(self, duration_seconds=120):
        """Run fatigue simulation for specified duration."""
        print(f"\n🧪 FATIGUE ANALYSIS SIMULATION")
        print("=" * 60)
        print(f"Duration: {duration_seconds} seconds")
        print("Simulating gradual fatigue onset...\n")
        
        self.simulation_running = True
        self.start_time = time.time()
        
        # Alert callback
        def alert_callback(alert_response):
            alert_level = alert_response['alert_level']
            if alert_level != 'none':
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n🚨 [{timestamp}] ALERT: {alert_level.upper()}")
                print(f"   Message: {alert_response['message']}")
                
                if alert_response.get('action_required'):
                    print(f"   ⚠️  ACTION: {alert_response['recommendation']}")
                
                self.alert_history.append({
                    'time': time.time() - self.start_time,
                    'alert': alert_response
                })
        
        # Store callback for manual triggering
        self.alert_callback = alert_callback
        
        # Main simulation loop
        try:
            while self.simulation_running:
                elapsed = time.time() - self.start_time
                
                if elapsed > duration_seconds:
                    break
                
                # Simulate eye openness
                eye_openness = self.simulate_eye_openness(elapsed)
                
                # Update fatigue metrics
                current_time = time.time()
                metrics = self.fatigue_detector.update(eye_openness, current_time)
                
                # Update alert system
                alerts = self.alert_system.update(
                    perclos_percentage=metrics['perclos_percentage'],
                    fatigue_level=metrics['fatigue_level'],
                    blink_count=metrics['blink_rate'],
                    microsleep_count=metrics['microsleep_count']
                )
                
                # Trigger callback if alert level changed
                if hasattr(self, 'alert_callback') and alerts['alert_level'] != 'none':
                    self.alert_callback(alerts)
                
                # Store metrics
                self.metrics_history.append({
                    'time': elapsed,
                    'eye_openness': eye_openness,
                    'perclos': metrics['perclos_percentage'],
                    'fatigue_level': metrics['fatigue_level'],
                    'blinks': metrics['blink_rate'],
                    'microsleeps': metrics['microsleep_count']
                })
                
                # Display progress
                if int(elapsed) % 5 == 0 and int(elapsed) != int(elapsed - 0.1):
                    self._display_status(elapsed, metrics, alerts)
                
                # Simulate ~30 FPS
                time.sleep(0.033)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Simulation interrupted by user")
        
        finally:
            self.simulation_running = False
            self._display_summary()
    
    def _display_status(self, elapsed, metrics, alerts):
        """Display current status."""
        print(f"\n⏱️  Time: {elapsed:.0f}s")
        print(f"   PERCLOS: {metrics['perclos_percentage']:.1f}%")
        print(f"   Fatigue Level: {metrics['fatigue_level']}")
        print(f"   Blinks: {metrics['blink_rate']}")
        print(f"   Alert: {alerts['alert_level']}")
    
    def _display_summary(self):
        """Display simulation summary."""
        print("\n\n" + "=" * 60)
        print("📊 SIMULATION SUMMARY")
        print("=" * 60)
        
        if not self.metrics_history:
            print("No data collected")
            return
        
        # Calculate statistics
        perclos_values = [m['perclos'] for m in self.metrics_history]
        avg_perclos = np.mean(perclos_values)
        max_perclos = np.max(perclos_values)
        
        total_blinks = max(m['blinks'] for m in self.metrics_history)
        total_microsleeps = max(m['microsleeps'] for m in self.metrics_history)
        
        print(f"\n📈 Metrics:")
        print(f"   Average PERCLOS: {avg_perclos:.1f}%")
        print(f"   Maximum PERCLOS: {max_perclos:.1f}%")
        print(f"   Total Blinks: {total_blinks}")
        print(f"   Total Microsleeps: {total_microsleeps}")
        
        print(f"\n🚨 Alerts:")
        if self.alert_history:
            for alert_event in self.alert_history:
                time_str = f"{alert_event['time']:.1f}s"
                level = alert_event['alert']['alert_level']
                print(f"   {time_str}: {level.upper()}")
        else:
            print("   No alerts triggered")
        
        # Show fatigue progression
        print(f"\n📉 Fatigue Progression:")
        time_points = [0, 30, 60, 90, 120]
        for t in time_points:
            if t < len(self.metrics_history) / 30:  # Approximate
                idx = int(t * 30)
                if idx < len(self.metrics_history):
                    perclos = self.metrics_history[idx]['perclos']
                    level = self.metrics_history[idx]['fatigue_level']
                    print(f"   {t}s: PERCLOS={perclos:.1f}%, Level={level}")


def test_with_real_camera():
    """Test with real camera validation first."""
    print("🎯 TESTING WITH FOUNDATION VALIDATION")
    print("=" * 60)
    
    # Validate foundation first
    print("\n1️⃣ Validating camera foundation...")
    if not validator.validate_layer('foundation'):
        print("❌ Camera validation failed!")
        print("   Please ensure camera is connected")
        return False
    
    print("✅ Foundation validated\n")
    
    # Create test instance
    tester = FatigueAnalysisTest()
    
    # This should work (foundation validated)
    try:
        tester.validate_camera()
    except RuntimeError as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Run simulation
    print("\n2️⃣ Running fatigue simulation...")
    tester.run_simulation(duration_seconds=60)  # 1 minute test
    
    return True


def test_algorithms_only():
    """Test fatigue algorithms without camera."""
    print("🧠 TESTING FATIGUE ALGORITHMS")
    print("=" * 60)
    print("(Camera validation skipped for algorithm testing)")
    
    tester = FatigueAnalysisTest()
    
    print("\n📊 Testing specific scenarios...")
    
    # Test 1: Alert person
    print("\n1️⃣ Alert person scenario")
    detector = FatigueDetector()
    detector.set_calibration('real')
    
    for _ in range(100):
        openness = 0.12 + random.gauss(0, 0.01)  # Alert range
        metrics = detector.update(openness, time.time())
        time.sleep(0.01)
    
    print(f"   PERCLOS: {metrics['perclos_percentage']:.1f}%")
    print(f"   Expected: <10% (Alert)")
    
    # Test 2: Drowsy person
    print("\n2️⃣ Drowsy person scenario")
    detector2 = FatigueDetector()
    detector2.set_calibration('real')
    
    for _ in range(100):
        openness = 0.06 + random.gauss(0, 0.01)  # Drowsy range
        metrics = detector2.update(openness, time.time())
        time.sleep(0.01)
    
    print(f"   PERCLOS: {metrics['perclos_percentage']:.1f}%")
    print(f"   Expected: 20-40% (Drowsy)")
    
    # Test 3: Microsleep detection
    print("\n3️⃣ Microsleep detection")
    detector3 = FatigueDetector()
    detector3.set_calibration('real')
    
    # Simulate microsleep
    for i in range(100):
        if 40 <= i <= 50:  # Microsleep period
            openness = 0.02
        else:
            openness = 0.12
        metrics = detector3.update(openness, time.time())
        time.sleep(0.01)
    
    print(f"   Microsleeps detected: {metrics['microsleep_count']}")
    print(f"   Expected: ≥1")


def main():
    """Run fatigue analysis tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test fatigue analysis system')
    parser.add_argument('--no-camera', action='store_true', 
                       help='Skip camera validation for algorithm testing')
    parser.add_argument('--duration', type=int, default=60,
                       help='Simulation duration in seconds (default: 60)')
    
    args = parser.parse_args()
    
    try:
        if args.no_camera:
            test_algorithms_only()
        else:
            # Try with camera first
            if not test_with_real_camera():
                print("\n⚠️  Falling back to algorithm testing...")
                test_algorithms_only()
        
        print("\n✅ Fatigue analysis test complete!")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())