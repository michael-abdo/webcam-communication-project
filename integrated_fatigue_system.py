#!/usr/bin/env python3
"""
Integrated Fatigue Detection System with Foundation-First Architecture

This system builds on the solid camera foundation, ensuring camera health
is validated before running advanced fatigue detection features.
"""

import sys
import os
import time
import json
import threading
from datetime import datetime

# Add camera tools to path
sys.path.append('./camera_tools/tests')
sys.path.append('./camera_tools/health_monitoring')
sys.path.append('./cognitive_overload/processing')

# Foundation imports
from quick_camera_test import test_camera, main as run_camera_test
from webcam_health_monitor import WebcamHealthMonitor

# Advanced feature imports
import cv2
import numpy as np
from flask import Flask, render_template_string, jsonify, Response
from landmark_processor import LandmarkProcessor
from landmark_mapping import CognitiveLandmarkMapper
from fatigue_metrics import FatigueDetector
from alert_system import AlertSystem

app = Flask(__name__)

# Global state - combines camera foundation and fatigue detection
system_state = {
    # Foundation layer
    'foundation_healthy': False,
    'camera_index': 0,
    'camera': None,
    'current_frame': None,
    'frame_lock': threading.Lock(),
    
    # Health monitoring layer
    'health_monitor': None,
    'camera_metrics': {},
    
    # Fatigue detection layer
    'running': False,
    'current_fatigue_metrics': {},
    'alert_status': {},
    'perclos_history': [],
    'session_start_time': None,
    'frame_count': 0,
    
    # System status
    'status_message': 'System not started',
    'layer_status': {
        'foundation': 'untested',
        'health': 'inactive',
        'streaming': 'inactive',
        'fatigue': 'inactive'
    }
}

# Initialize components
monitor_thread = None
monitoring = False
fatigue_components = {}

def validate_foundation():
    """
    FOUNDATION RULE: Validate camera health before any operations.
    Returns True if foundation is solid, False otherwise.
    """
    print("\n🏗️  VALIDATING FOUNDATION...")
    print("=" * 50)
    
    # Test camera 0
    camera_healthy = test_camera(0)
    
    if camera_healthy:
        system_state['foundation_healthy'] = True
        system_state['layer_status']['foundation'] = 'healthy'
        system_state['status_message'] = 'Foundation validated - camera healthy'
        print("✅ FOUNDATION SOLID - Camera test passed")
        return True
    else:
        system_state['foundation_healthy'] = False
        system_state['layer_status']['foundation'] = 'failed'
        system_state['status_message'] = 'FOUNDATION FAILED - Camera not working'
        print("❌ FOUNDATION FAILED - Cannot proceed without working camera")
        return False

def initialize_health_monitor():
    """Initialize health monitoring layer (depends on foundation)."""
    if not system_state['foundation_healthy']:
        print("❌ Cannot initialize health monitor - foundation not validated")
        return False
    
    try:
        system_state['health_monitor'] = WebcamHealthMonitor()
        system_state['layer_status']['health'] = 'active'
        print("✅ Health monitoring initialized")
        return True
    except Exception as e:
        print(f"❌ Health monitor initialization failed: {e}")
        system_state['layer_status']['health'] = 'failed'
        return False

def initialize_fatigue_detection():
    """Initialize fatigue detection components (depends on all lower layers)."""
    if system_state['layer_status']['foundation'] != 'healthy':
        print("❌ Cannot initialize fatigue detection - foundation not healthy")
        return False
    
    try:
        # Initialize MediaPipe and fatigue components
        fatigue_components['mapper'] = CognitiveLandmarkMapper()
        fatigue_components['fatigue_detector'] = FatigueDetector()
        fatigue_components['fatigue_detector'].set_calibration('real')
        fatigue_components['alert_system'] = AlertSystem()
        fatigue_components['processor'] = LandmarkProcessor()
        
        system_state['layer_status']['fatigue'] = 'ready'
        print("✅ Fatigue detection components initialized")
        return True
    except Exception as e:
        print(f"❌ Fatigue detection initialization failed: {e}")
        system_state['layer_status']['fatigue'] = 'failed'
        return False

def monitor_camera_with_fatigue():
    """
    Combined monitoring thread that maintains camera health and performs fatigue detection.
    Uses single-source camera architecture from foundation.
    """
    global system_state, monitoring
    
    # Open camera (single source)
    cap = cv2.VideoCapture(system_state['camera_index'])
    
    if not cap.isOpened():
        system_state['status_message'] = 'Camera failed to open'
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    system_state['camera'] = cap
    system_state['session_start_time'] = time.time()
    frame_times = []
    
    while monitoring:
        start_time = time.time()
        ret, frame = cap.read()
        
        if not ret or frame is None:
            continue
        
        # Store frame in shared buffer (foundation pattern)
        with system_state['frame_lock']:
            system_state['current_frame'] = frame.copy()
        
        system_state['frame_count'] += 1
        
        # Calculate basic metrics (health layer)
        brightness = np.mean(frame)
        frame_time = time.time() - start_time
        frame_times.append(frame_time)
        if len(frame_times) > 30:
            frame_times.pop(0)
        
        system_state['camera_metrics'] = {
            'brightness': round(brightness, 2),
            'fps': round(1 / np.mean(frame_times), 1) if frame_times else 0,
            'resolution': f"{frame.shape[1]}x{frame.shape[0]}"
        }
        
        # Perform fatigue detection if components ready
        if system_state['layer_status']['fatigue'] == 'ready' and system_state['running']:
            try:
                # Process with MediaPipe
                results = fatigue_components['processor'].process_static(frame)
                
                if results and results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        # Calculate eye openness
                        mapper = fatigue_components['mapper']
                        left_eye = mapper.calculate_eye_openness(face_landmarks, 'left')
                        right_eye = mapper.calculate_eye_openness(face_landmarks, 'right')
                        avg_openness = (left_eye + right_eye) / 2
                        
                        # Update fatigue metrics
                        fatigue_metrics = fatigue_components['fatigue_detector'].update(
                            avg_openness, time.time()
                        )
                        
                        # Update alert system
                        alerts = fatigue_components['alert_system'].update(
                            perclos_percentage=fatigue_metrics['perclos_percentage'],
                            fatigue_level=fatigue_metrics['fatigue_level'],
                            blink_count=fatigue_metrics['blink_rate'],
                            microsleep_count=fatigue_metrics['microsleep_count']
                        )
                        
                        # Store current state
                        system_state['current_fatigue_metrics'] = fatigue_metrics
                        system_state['alert_status'] = alerts
                        
                        # Update history
                        system_state['perclos_history'].append({
                            'timestamp': time.time(),
                            'value': fatigue_metrics['perclos_percentage']
                        })
                        
                        # Keep history manageable
                        if len(system_state['perclos_history']) > 100:
                            system_state['perclos_history'].pop(0)
                
            except Exception as e:
                print(f"Fatigue detection error: {e}")
        
        time.sleep(0.033)  # ~30 FPS
    
    cap.release()
    system_state['camera'] = None

# Web routes
@app.route('/')
def dashboard():
    """Main integrated dashboard."""
    return render_template_string(INTEGRATED_DASHBOARD_HTML)

@app.route('/api/validate_foundation', methods=['POST'])
def api_validate_foundation():
    """Validate camera foundation before starting system."""
    success = validate_foundation()
    
    if success:
        # Initialize higher layers
        initialize_health_monitor()
        initialize_fatigue_detection()
    
    return jsonify({
        'success': success,
        'status': system_state['status_message'],
        'layers': system_state['layer_status']
    })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start integrated monitoring (requires foundation validation)."""
    global monitor_thread, monitoring
    
    if not system_state['foundation_healthy']:
        return jsonify({
            'success': False,
            'error': 'Foundation not validated. Run foundation check first.'
        })
    
    if monitoring:
        return jsonify({'status': 'already running'})
    
    monitoring = True
    system_state['running'] = True
    system_state['layer_status']['streaming'] = 'active'
    
    monitor_thread = threading.Thread(target=monitor_camera_with_fatigue)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring."""
    global monitoring
    
    monitoring = False
    system_state['running'] = False
    system_state['layer_status']['streaming'] = 'inactive'
    
    return jsonify({'status': 'stopped'})

@app.route('/api/status')
def get_status():
    """Get comprehensive system status."""
    return jsonify({
        'foundation_healthy': system_state['foundation_healthy'],
        'layers': system_state['layer_status'],
        'running': system_state['running'],
        'frame_count': system_state['frame_count'],
        'camera_metrics': system_state['camera_metrics'],
        'fatigue_metrics': system_state['current_fatigue_metrics'],
        'alert_status': system_state['alert_status'],
        'status_message': system_state['status_message']
    })

@app.route('/video_feed')
def video_feed():
    """Video streaming using shared frame buffer pattern."""
    def generate_frames():
        while True:
            if not monitoring:
                # Show placeholder
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Start Monitoring to View Feed", 
                           (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                ret, buffer = cv2.imencode('.jpg', placeholder)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.5)
                continue
            
            # Get frame from shared buffer
            frame = None
            with system_state['frame_lock']:
                if system_state['current_frame'] is not None:
                    frame = system_state['current_frame'].copy()
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Add overlays
            cv2.putText(frame, f"FPS: {system_state['camera_metrics'].get('fps', 0)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if system_state['current_fatigue_metrics']:
                metrics = system_state['current_fatigue_metrics']
                cv2.putText(frame, f"PERCLOS: {metrics.get('perclos_percentage', 0):.1f}%", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if system_state['alert_status'].get('alert_level') != 'none':
                    alert_color = (0, 255, 255) if system_state['alert_status']['alert_level'] == 'warning' else (0, 0, 255)
                    cv2.putText(frame, f"ALERT: {system_state['alert_status']['alert_level'].upper()}", 
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, alert_color, 2)
            
            # Encode and yield
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)
    
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Dashboard HTML
INTEGRATED_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Integrated Fatigue Detection System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .foundation-status {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .layer-indicator {
            display: inline-block;
            padding: 5px 15px;
            margin: 5px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        .layer-healthy { background: #4CAF50; color: white; }
        .layer-active { background: #2196F3; color: white; }
        .layer-ready { background: #FF9800; color: white; }
        .layer-inactive { background: #9E9E9E; color: white; }
        .layer-failed { background: #F44336; color: white; }
        .layer-untested { background: #607D8B; color: white; }
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background-color: #45a049; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        .validate-btn { background-color: #FF5722; }
        .validate-btn:hover { background-color: #E64A19; }
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        .video-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metrics-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #video-feed {
            max-width: 100%;
            border-radius: 5px;
        }
        .metric {
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .metric-label {
            font-weight: bold;
            color: #666;
        }
        .metric-value {
            font-size: 24px;
            color: #333;
        }
        .alert-active {
            background: #FFF3E0;
            border: 2px solid #FF9800;
        }
        .alert-critical {
            background: #FFEBEE;
            border: 2px solid #F44336;
        }
        .status-message {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status-success { background: #E8F5E9; color: #2E7D32; }
        .status-error { background: #FFEBEE; color: #C62828; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ Integrated Fatigue Detection System</h1>
        <p>Foundation-First Architecture with Advanced Analysis</p>
    </div>
    
    <div class="foundation-status">
        <h2>System Architecture Status</h2>
        <div id="layer-status">
            <span class="layer-indicator layer-untested">Foundation: Untested</span>
            <span class="layer-indicator layer-inactive">Health: Inactive</span>
            <span class="layer-indicator layer-inactive">Streaming: Inactive</span>
            <span class="layer-indicator layer-inactive">Fatigue: Inactive</span>
        </div>
        <div id="status-message" class="status-message" style="display:none;"></div>
    </div>
    
    <div class="controls">
        <button onclick="validateFoundation()" class="validate-btn">🎯 Validate Foundation</button>
        <button onclick="startSystem()" id="start-btn" disabled>▶️ Start System</button>
        <button onclick="stopSystem()" id="stop-btn" disabled>⏸️ Stop System</button>
    </div>
    
    <div class="main-content">
        <div class="video-container">
            <h2>📹 Live Camera Feed</h2>
            <img id="video-feed" src="/video_feed" style="display:block;">
        </div>
        
        <div class="metrics-container">
            <h2>📊 System Metrics</h2>
            
            <div class="metric">
                <div class="metric-label">Camera Health</div>
                <div class="metric-value" id="camera-fps">-- FPS</div>
            </div>
            
            <div class="metric">
                <div class="metric-label">Brightness</div>
                <div class="metric-value" id="brightness">--</div>
            </div>
            
            <div class="metric" id="perclos-metric">
                <div class="metric-label">PERCLOS</div>
                <div class="metric-value" id="perclos">--%</div>
            </div>
            
            <div class="metric" id="fatigue-metric">
                <div class="metric-label">Fatigue Level</div>
                <div class="metric-value" id="fatigue-level">None</div>
            </div>
            
            <div class="metric" id="alert-metric">
                <div class="metric-label">Alert Status</div>
                <div class="metric-value" id="alert-status">None</div>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        let foundationValidated = false;
        
        function validateFoundation() {
            showStatus('Validating camera foundation...', 'info');
            
            fetch('/api/validate_foundation', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    foundationValidated = data.success;
                    updateLayerStatus(data.layers);
                    
                    if (data.success) {
                        showStatus('✅ Foundation validated! System ready.', 'success');
                        document.getElementById('start-btn').disabled = false;
                    } else {
                        showStatus('❌ Foundation validation failed! Check camera.', 'error');
                        document.getElementById('start-btn').disabled = true;
                    }
                });
        }
        
        function startSystem() {
            if (!foundationValidated) {
                showStatus('Please validate foundation first!', 'error');
                return;
            }
            
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success === false) {
                        showStatus(data.error, 'error');
                        return;
                    }
                    
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    startUpdating();
                    showStatus('System started', 'success');
                });
        }
        
        function stopSystem() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    stopUpdating();
                    showStatus('System stopped', 'info');
                });
        }
        
        function updateLayerStatus(layers) {
            const container = document.getElementById('layer-status');
            container.innerHTML = '';
            
            const layerNames = {
                'foundation': 'Foundation',
                'health': 'Health',
                'streaming': 'Streaming',
                'fatigue': 'Fatigue'
            };
            
            for (const [layer, status] of Object.entries(layers)) {
                const span = document.createElement('span');
                span.className = `layer-indicator layer-${status}`;
                span.textContent = `${layerNames[layer]}: ${status}`;
                container.appendChild(span);
            }
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status-message');
            statusDiv.textContent = message;
            statusDiv.className = 'status-message status-' + (type === 'error' ? 'error' : 'success');
            statusDiv.style.display = 'block';
            
            if (type !== 'error') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 5000);
            }
        }
        
        function updateMetrics() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update layer status
                    updateLayerStatus(data.layers);
                    
                    // Update camera metrics
                    if (data.camera_metrics.fps) {
                        document.getElementById('camera-fps').textContent = data.camera_metrics.fps + ' FPS';
                        document.getElementById('brightness').textContent = data.camera_metrics.brightness;
                    }
                    
                    // Update fatigue metrics
                    if (data.fatigue_metrics.perclos_percentage !== undefined) {
                        document.getElementById('perclos').textContent = 
                            data.fatigue_metrics.perclos_percentage.toFixed(1) + '%';
                        document.getElementById('fatigue-level').textContent = 
                            data.fatigue_metrics.fatigue_level || 'Normal';
                    }
                    
                    // Update alert status
                    if (data.alert_status.alert_level) {
                        const alertLevel = data.alert_status.alert_level;
                        document.getElementById('alert-status').textContent = 
                            alertLevel.charAt(0).toUpperCase() + alertLevel.slice(1);
                        
                        // Update alert styling
                        const alertMetric = document.getElementById('alert-metric');
                        alertMetric.className = 'metric';
                        if (alertLevel === 'warning') {
                            alertMetric.classList.add('alert-active');
                        } else if (alertLevel === 'critical' || alertLevel === 'emergency') {
                            alertMetric.classList.add('alert-critical');
                        }
                    }
                });
        }
        
        function startUpdating() {
            updateMetrics();
            updateInterval = setInterval(updateMetrics, 1000);
        }
        
        function stopUpdating() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }
        
        // Check initial status
        updateMetrics();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🏗️  INTEGRATED FATIGUE DETECTION SYSTEM")
    print("=" * 50)
    print("Foundation-First Architecture with Advanced Analysis")
    print("\nStarting web interface at: http://localhost:5000")
    print("\nIMPORTANT: Click 'Validate Foundation' before starting!")
    print("This ensures camera health before running advanced features.")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)