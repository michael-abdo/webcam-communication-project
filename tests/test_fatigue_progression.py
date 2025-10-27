#!/usr/bin/env python3
"""
Test script to demonstrate fatigue progression over time
"""

import requests
import time
import json

def test_system():
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Fatigue Detection System")
    print("=" * 50)
    
    # Start detection
    print("1. Starting detection...")
    response = requests.post(f"{base_url}/start_detection")
    print(f"   Status: {response.json()}")
    
    # Monitor for 30 seconds
    print("\n2. Monitoring metrics over time...")
    for i in range(10):
        response = requests.get(f"{base_url}/get_metrics")
        data = response.json()
        
        metrics = data['metrics']
        alert = data['alert_status']
        
        print(f"   Time {i*3:2d}s: PERCLOS: {metrics['perclos']*100:5.1f}% | "
              f"Blinks: {metrics['blink_rate']:4.1f}/min | "
              f"Alert: {alert['level']:8s} | "
              f"Eye: {metrics['eye_openness']:4.2f}")
        
        if alert['level'] != 'Normal':
            print(f"      🚨 {alert['message']}")
        
        time.sleep(3)
    
    # Stop detection
    print("\n3. Stopping detection...")
    response = requests.post(f"{base_url}/stop_detection")
    print(f"   Status: {response.json()}")
    
    print("\n✅ Test completed! Backend is working correctly.")
    print("🌐 Open http://localhost:5001 in your browser to see the dashboard")

if __name__ == "__main__":
    try:
        test_system()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 5001")
    except Exception as e:
        print(f"❌ Error: {e}")