#!/usr/bin/env python3
"""
Simplified Fatigue Detection Backend
Works without MediaPipe for demonstration purposes
"""

import json
import time
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, Response

app = Flask(__name__)

# Global state for demo
demo_state = {
    'running': False,
    'current_metrics': {},
    'alert_status': {},
    'perclos_history': [],
    'blink_history': [],
    'session_start_time': None,
    'frame_count': 0,
    'camera': None
}

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start detection endpoint for frontend."""
    global demo_state
    
    demo_state['running'] = True
    demo_state['session_start_time'] = time.time()
    demo_state['frame_count'] = 0
    demo_state['perclos_history'] = []
    demo_state['blink_history'] = []
    
    return jsonify({'status': 'success', 'message': 'Detection started'})

@app.route('/stop_detection', methods=['POST'])  
def stop_detection():
    """Stop detection endpoint for frontend."""
    global demo_state
    
    demo_state['running'] = False
    
    return jsonify({'status': 'success', 'message': 'Detection stopped'})

@app.route('/reset_metrics', methods=['POST'])
def reset_metrics():
    """Reset all metrics."""
    global demo_state
    demo_state['current_metrics'] = {}
    demo_state['alert_status'] = {}
    demo_state['perclos_history'] = []
    demo_state['blink_history'] = []
    demo_state['frame_count'] = 0
    demo_state['session_start_time'] = time.time() if demo_state['running'] else None
    return jsonify({'status': 'success', 'message': 'Metrics reset'})

@app.route('/get_metrics')
def get_metrics_frontend():
    """Get metrics for frontend (simplified format with simulated data)."""
    
    if demo_state['running']:
        # Simulate fatigue detection metrics
        session_time = time.time() - demo_state['session_start_time']
        demo_state['frame_count'] += 1
        
        # Simulate realistic fatigue patterns
        base_perclos = 0.15 + (session_time / 600) * 0.3  # Gradually increase fatigue
        noise = random.uniform(-0.05, 0.05)
        perclos = max(0, min(1, base_perclos + noise))
        
        eye_openness = 1.0 - (perclos * 0.8) + random.uniform(-0.1, 0.1)
        eye_openness = max(0.2, min(1.0, eye_openness))
        
        blink_rate = 15 + (perclos * 20) + random.uniform(-3, 3)
        blink_rate = max(5, blink_rate)
        
        # Determine alert level
        if perclos < 0.2:
            alert_level = 'Normal'
            alert_message = 'All systems normal'
        elif perclos < 0.5:
            alert_level = 'Warning'
            alert_message = 'Mild fatigue detected - consider taking a break'
        else:
            alert_level = 'Critical'
            alert_message = 'High fatigue detected - immediate break recommended'
        
        response = {
            'metrics': {
                'perclos': perclos,
                'blink_rate': blink_rate,
                'eye_openness': eye_openness,
            },
            'alert_status': {
                'level': alert_level,
                'message': alert_message
            },
            'frame_count': demo_state['frame_count'],
            'fps': 30.0
        }
        
        # Store for history
        demo_state['current_metrics'] = response['metrics']
        demo_state['alert_status'] = response['alert_status']
    
    else:
        # System not running
        response = {
            'metrics': {
                'perclos': 0.0,
                'blink_rate': 0.0,
                'eye_openness': 1.0,
            },
            'alert_status': {
                'level': 'Normal',
                'message': 'System not running'
            },
            'frame_count': demo_state.get('frame_count', 0),
            'fps': 0.0
        }
    
    return jsonify(response)

@app.route('/api/metrics')
def get_api_metrics():
    """API endpoint for detailed metrics."""
    return jsonify({
        'current_metrics': demo_state['current_metrics'],
        'alert_status': demo_state['alert_status'],
        'perclos_history': demo_state['perclos_history'][-60:],
        'session_duration': time.time() - demo_state['session_start_time'] if demo_state['session_start_time'] else 0,
        'frame_count': demo_state['frame_count'],
        'running': demo_state['running']
    })

@app.route('/status')
def status():
    """System status endpoint."""
    return jsonify({
        'status': 'running' if demo_state['running'] else 'stopped',
        'timestamp': datetime.now().isoformat(),
        'system': 'Fatigue Detection System v1.0',
        'features': [
            'PERCLOS calculation',
            'Real-time alerts',
            'Progressive warning system',
            'Session tracking'
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting Simplified Fatigue Detection Backend...")
    print("📊 Demo system with simulated metrics")
    print("🌐 Access dashboard at: http://localhost:5001")
    print("\nFeatures:")
    print("  ✅ Simulated PERCLOS calculation")
    print("  ✅ Progressive alert system") 
    print("  ✅ Real-time metric updates")
    print("  ✅ Session tracking")
    print("  ✅ REST API endpoints")
    
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)