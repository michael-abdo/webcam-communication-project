#!/usr/bin/env python3
"""
Basic Fatigue Detection Dashboard

Works without MediaPipe - uses simple motion detection
and simulated fatigue metrics for demonstration.
"""

import cv2
import numpy as np
import time
import json
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response

app = Flask(__name__)

# Global state with shared frame buffer
dashboard_state = {
    'running': False,
    'camera': None,
    'start_time': None,
    'frame_count': 0,
    'current_metrics': {
        'perclos': 0.0,
        'blink_count': 0,
        'fatigue_level': 'ALERT',
        'eye_openness': 1.0,
        'alert_level': 'normal',
        'motion_level': 0.0
    },
    'perclos_history': [],
    'previous_frame': None,
    'current_frame': None,  # Shared frame buffer
    'frame_lock': threading.Lock()  # Thread synchronization
}

# Camera monitoring thread
monitor_thread = None

def monitor_camera():
    """Background thread to monitor camera and capture frames with fatigue detection."""
    global dashboard_state, monitor_thread
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    
    while dashboard_state['running']:
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect motion and update metrics
        motion_level = detect_motion(frame)
        
        # Simulate fatigue progression
        perclos, fatigue_level, alert_level = simulate_fatigue_progression()
        
        # Simulate blink counting (based on motion)
        blink_count = dashboard_state['frame_count'] // 120  # One "blink" every 4 seconds
        
        # Update metrics
        dashboard_state['current_metrics'] = {
            'perclos': perclos,
            'blink_count': blink_count,
            'fatigue_level': fatigue_level,
            'eye_openness': 1.0 - (perclos / 100),
            'alert_level': alert_level,
            'motion_level': motion_level
        }
        
        dashboard_state['frame_count'] += 1
        
        # Add to history every 30 frames (1 second)
        if dashboard_state['frame_count'] % 30 == 0:
            dashboard_state['perclos_history'].append({
                'timestamp': time.time(),
                'perclos': perclos,
                'alert_level': alert_level
            })
            
            # Keep only last 5 minutes of data
            if len(dashboard_state['perclos_history']) > 300:
                dashboard_state['perclos_history'].pop(0)
        
        # Draw metrics overlay
        frame_with_overlay = frame.copy()
        draw_metrics(frame_with_overlay, dashboard_state['current_metrics'])
        
        # Store frame in shared buffer with thread safety
        with dashboard_state['frame_lock']:
            dashboard_state['current_frame'] = frame_with_overlay.copy()
        
        time.sleep(0.033)  # ~30 FPS
    
    cap.release()


# Simulated fatigue detection
def simulate_fatigue_progression():
    """Simulate gradual fatigue based on session duration."""
    if not dashboard_state['start_time']:
        return 0.0, 'ALERT', 'normal'
    
    # Get session duration in minutes
    session_duration = (time.time() - dashboard_state['start_time']) / 60
    
    # Simulate fatigue increasing over time
    base_fatigue = min(40.0, session_duration * 2)  # 2% per minute, max 40%
    
    # Add some random variation
    import random
    variation = random.gauss(0, 2)
    perclos = max(0, base_fatigue + variation)
    
    # Determine levels
    if perclos < 10:
        fatigue_level = 'ALERT'
        alert_level = 'normal'
    elif perclos < 20:
        fatigue_level = 'TIRED'
        alert_level = 'warning'
    elif perclos < 30:
        fatigue_level = 'DROWSY'
        alert_level = 'critical'
    else:
        fatigue_level = 'DANGER'
        alert_level = 'emergency'
    
    return perclos, fatigue_level, alert_level


def detect_motion(frame):
    """Simple motion detection to simulate activity level."""
    global dashboard_state
    
    if dashboard_state['previous_frame'] is None:
        dashboard_state['previous_frame'] = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return 0.0
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate difference
    diff = cv2.absdiff(dashboard_state['previous_frame'], gray)
    
    # Calculate motion level
    motion_level = np.mean(diff) / 255.0
    
    # Update previous frame
    dashboard_state['previous_frame'] = gray
    
    return motion_level


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/start', methods=['POST'])
def start_detection():
    """Start fatigue detection."""
    global dashboard_state, monitor_thread
    
    try:
        if dashboard_state['running']:
            return jsonify({'success': True, 'message': 'Detection already running'})
        
        dashboard_state['running'] = True
        dashboard_state['start_time'] = time.time()
        dashboard_state['frame_count'] = 0
        dashboard_state['perclos_history'] = []
        dashboard_state['previous_frame'] = None
        dashboard_state['current_frame'] = None
        
        # Start camera monitoring thread
        monitor_thread = threading.Thread(target=monitor_camera, daemon=True)
        monitor_thread.start()
        
        return jsonify({'success': True, 'message': 'Detection started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stop', methods=['POST'])
def stop_detection():
    """Stop fatigue detection."""
    global dashboard_state, monitor_thread
    
    dashboard_state['running'] = False
    
    # Wait for monitor thread to finish
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=2.0)
    
    return jsonify({'success': True, 'message': 'Detection stopped'})


@app.route('/api/metrics')
def get_metrics():
    """Get current metrics."""
    uptime = 0
    if dashboard_state['start_time']:
        uptime = round(time.time() - dashboard_state['start_time'], 1)
    
    return jsonify({
        'running': dashboard_state['running'],
        'uptime': uptime,
        'frame_count': dashboard_state['frame_count'],
        'metrics': dashboard_state['current_metrics'],
        'perclos_history': dashboard_state['perclos_history'][-60:]  # Last 60 points
    })


def generate_frames():
    """Generate frames for video streaming using shared camera buffer."""
    
    while True:
        # Check if monitoring is active and frames are available
        if not dashboard_state['running']:
            # If monitoring stopped, show placeholder frame
            placeholder_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder_frame, "Click Start Detection to View Feed", 
                       (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', placeholder_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.5)  # Reduce frame rate for placeholder
            continue
        
        # Get current frame from shared buffer with thread safety
        frame = None
        with dashboard_state['frame_lock']:
            if dashboard_state['current_frame'] is not None:
                frame = dashboard_state['current_frame'].copy()
        
        if frame is None:
            # No frame available yet, wait briefly
            time.sleep(0.1)
            continue
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS


def draw_metrics(frame, metrics):
    """Draw metrics overlay on frame."""
    
    # Color based on alert level
    colors = {
        'normal': (0, 255, 0),     # Green
        'warning': (0, 255, 255),  # Yellow
        'critical': (0, 165, 255), # Orange
        'emergency': (0, 0, 255)   # Red
    }
    
    color = colors.get(metrics['alert_level'], (255, 255, 255))
    
    # Draw background
    cv2.rectangle(frame, (10, 10), (450, 220), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (450, 220), color, 2)
    
    # Draw text
    y = 40
    cv2.putText(frame, f"PERCLOS: {metrics['perclos']:.1f}%", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y += 30
    cv2.putText(frame, f"Fatigue: {metrics['fatigue_level']}", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y += 30
    cv2.putText(frame, f"Eye Openness: {metrics['eye_openness']:.3f}", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y += 30
    cv2.putText(frame, f"Blinks: {metrics['blink_count']}", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y += 30
    cv2.putText(frame, f"Motion: {metrics['motion_level']:.3f}", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y += 30
    cv2.putText(frame, f"Alert: {metrics['alert_level'].upper()}", 
                (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Draw warning if critical
    if metrics['alert_level'] in ['critical', 'emergency']:
        cv2.putText(frame, "ATTENTION REQUIRED!", 
                    (20, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    
    # Draw session info
    if dashboard_state['start_time']:
        session_time = int(time.time() - dashboard_state['start_time'])
        minutes = session_time // 60
        seconds = session_time % 60
        cv2.putText(frame, f"Session: {minutes}:{seconds:02d}", 
                    (frame.shape[1] - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Basic Fatigue Detection Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .header {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        button {
            padding: 12px 24px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        .start-btn {
            background-color: #4CAF50;
            color: white;
        }
        .stop-btn {
            background-color: #f44336;
            color: white;
        }
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .video-container, .metrics-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #video-feed {
            max-width: 100%;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        .metric-item {
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .metric-label {
            font-weight: bold;
            color: #555;
        }
        .metric-value {
            color: #333;
        }
        .alert-normal { background-color: #e8f5e9; }
        .alert-warning { background-color: #fff3cd; }
        .alert-critical { background-color: #ffecb5; }
        .alert-emergency { background-color: #ffcccb; }
        .status {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status-running { background: #e8f5e9; color: #2e7d32; }
        .status-stopped { background: #ffebee; color: #c62828; }
        .demo-notice {
            background: #e3f2fd;
            border: 2px solid #2196f3;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .chart-placeholder {
            height: 150px;
            background: #f5f5f5;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Basic Fatigue Detection Dashboard</h1>
        <p>Simulated PERCLOS monitoring with progressive fatigue</p>
    </div>
    
    <div class="demo-notice">
        <strong>📋 Demo Mode Active</strong><br>
        Fatigue increases gradually over time to demonstrate alert progression<br>
        <small>In production, this would use real face tracking with MediaPipe</small>
    </div>
    
    <div class="controls">
        <button class="start-btn" onclick="startDetection()">▶️ Start Detection</button>
        <button class="stop-btn" onclick="stopDetection()">⏹️ Stop Detection</button>
    </div>
    
    <div id="status" class="status status-stopped">Ready to start</div>
    
    <div class="main-content">
        <div class="video-container">
            <h2>📹 Live Video with Metrics Overlay</h2>
            <img id="video-feed" src="/video_feed" alt="Video Feed">
        </div>
        
        <div class="metrics-container">
            <h2>📊 Fatigue Metrics</h2>
            
            <div class="metric-item" id="perclos-metric">
                <span class="metric-label">PERCLOS:</span>
                <span class="metric-value">0.0%</span>
            </div>
            
            <div class="metric-item" id="fatigue-metric">
                <span class="metric-label">Fatigue Level:</span>
                <span class="metric-value">ALERT</span>
            </div>
            
            <div class="metric-item" id="openness-metric">
                <span class="metric-label">Eye Openness:</span>
                <span class="metric-value">1.000</span>
            </div>
            
            <div class="metric-item" id="blink-metric">
                <span class="metric-label">Blink Count:</span>
                <span class="metric-value">0</span>
            </div>
            
            <div class="metric-item" id="motion-metric">
                <span class="metric-label">Motion Level:</span>
                <span class="metric-value">0.000</span>
            </div>
            
            <div class="metric-item" id="alert-metric">
                <span class="metric-label">Alert Level:</span>
                <span class="metric-value">NORMAL</span>
            </div>
            
            <div class="metric-item" id="uptime-metric">
                <span class="metric-label">Session Time:</span>
                <span class="metric-value">0:00</span>
            </div>
            
            <div class="chart-placeholder">
                📈 PERCLOS Progression<br>
                <small>Watch fatigue levels increase over time</small>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        
        function startDetection() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('status').textContent = 'Detection running - fatigue simulation active';
                        document.getElementById('status').className = 'status status-running';
                        updateInterval = setInterval(updateMetrics, 1000);
                    } else {
                        alert('Error: ' + data.error);
                    }
                });
        }
        
        function stopDetection() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = 'Detection stopped';
                    document.getElementById('status').className = 'status status-stopped';
                    if (updateInterval) {
                        clearInterval(updateInterval);
                    }
                });
        }
        
        function updateMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.metrics) {
                        const m = data.metrics;
                        
                        // Update metric values
                        document.querySelector('#perclos-metric .metric-value').textContent = m.perclos.toFixed(1) + '%';
                        document.querySelector('#fatigue-metric .metric-value').textContent = m.fatigue_level;
                        document.querySelector('#openness-metric .metric-value').textContent = m.eye_openness.toFixed(3);
                        document.querySelector('#blink-metric .metric-value').textContent = m.blink_count;
                        document.querySelector('#motion-metric .metric-value').textContent = m.motion_level.toFixed(3);
                        document.querySelector('#alert-metric .metric-value').textContent = m.alert_level.toUpperCase();
                        
                        // Update alert styling
                        const alertMetric = document.getElementById('alert-metric');
                        alertMetric.className = 'metric-item alert-' + m.alert_level;
                    }
                    
                    if (data.uptime) {
                        const minutes = Math.floor(data.uptime / 60);
                        const seconds = Math.floor(data.uptime % 60);
                        document.querySelector('#uptime-metric .metric-value').textContent = 
                            minutes + ':' + seconds.toString().padStart(2, '0');
                    }
                });
        }
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("📊 BASIC FATIGUE DETECTION DASHBOARD")
    print("=" * 50)
    print("Simulated fatigue monitoring with progressive alerts")
    print("🌐 Access dashboard at: http://localhost:5001")
    print("\nFeatures:")
    print("  ✅ Progressive PERCLOS simulation")
    print("  ✅ Motion detection for activity level")
    print("  ✅ Gradual fatigue progression over time")
    print("  ✅ Live video with metrics overlay")
    print("  ✅ Alert level visualization")
    print("  ✅ Real-time metric updates")
    print("\n📋 Demo Mode: Fatigue increases 2% per minute")
    print("   Watch alert levels progress: ALERT → TIRED → DROWSY → DANGER")
    
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)