#!/usr/bin/env python3
"""
Real-time Camera Status Dashboard
Web-based dashboard for monitoring camera health and status
"""

import cv2
import json
import time
import threading
import numpy as np
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response

app = Flask(__name__)

# Global state for camera monitoring
camera_state = {
    'camera_index': 0,
    'is_active': False,
    'last_frame_time': 0,
    'frame_count': 0,
    'health_status': 'unknown',
    'metrics': {},
    'history': [],
    'current_frame': None,  # Shared frame buffer
    'frame_lock': threading.Lock()  # Thread synchronization
}

# Camera monitor thread
monitor_thread = None
monitoring = False

def monitor_camera():
    """
    Background thread to monitor camera health and capture frames.
    
    This thread maintains exclusive camera access and stores frames in a shared
    buffer for use by the video streaming endpoint, eliminating resource conflicts.
    """
    global camera_state, monitoring
    
    cap = cv2.VideoCapture(camera_state['camera_index'])
    
    if not cap.isOpened():
        camera_state['health_status'] = 'error'
        camera_state['is_active'] = False
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_times = []
    brightness_values = []
    
    while monitoring:
        start_time = time.time()
        ret, frame = cap.read()
        frame_time = time.time() - start_time
        
        if ret and frame is not None:
            camera_state['is_active'] = True
            camera_state['last_frame_time'] = time.time()
            camera_state['frame_count'] += 1
            
            # Store frame in shared buffer with thread safety
            with camera_state['frame_lock']:
                camera_state['current_frame'] = frame.copy()
            
            # Calculate metrics
            brightness = np.mean(frame)
            contrast = np.std(frame)
            
            frame_times.append(frame_time)
            brightness_values.append(brightness)
            
            # Keep only last 30 values
            if len(frame_times) > 30:
                frame_times.pop(0)
                brightness_values.pop(0)
            
            # Update metrics
            camera_state['metrics'] = {
                'brightness': round(brightness, 2),
                'contrast': round(contrast, 2),
                'avg_frame_time': round(np.mean(frame_times) * 1000, 2),  # ms
                'fps': round(1 / np.mean(frame_times), 1) if frame_times else 0,
                'resolution': f"{frame.shape[1]}x{frame.shape[0]}",
                'color_channels': frame.shape[2] if len(frame.shape) > 2 else 1
            }
            
            # Determine health status
            if brightness < 10:
                camera_state['health_status'] = 'dark'
            elif brightness > 245:
                camera_state['health_status'] = 'overexposed'
            elif camera_state['metrics']['fps'] < 5:
                camera_state['health_status'] = 'slow'
            else:
                camera_state['health_status'] = 'healthy'
            
            # Add to history
            if camera_state['frame_count'] % 10 == 0:  # Every 10 frames
                camera_state['history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'brightness': brightness,
                    'fps': camera_state['metrics']['fps'],
                    'status': camera_state['health_status']
                })
                
                # Keep only last 50 history entries
                if len(camera_state['history']) > 50:
                    camera_state['history'].pop(0)
        else:
            camera_state['is_active'] = False
            camera_state['health_status'] = 'no_frames'
        
        time.sleep(0.1)  # 10 Hz monitoring rate
    
    cap.release()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def get_status():
    """Get current camera status."""
    return jsonify({
        'camera_index': camera_state['camera_index'],
        'is_active': camera_state['is_active'],
        'health_status': camera_state['health_status'],
        'frame_count': camera_state['frame_count'],
        'last_update': time.time() - camera_state['last_frame_time'] if camera_state['last_frame_time'] else None,
        'metrics': camera_state['metrics'],
        'history_length': len(camera_state['history'])
    })

@app.route('/api/metrics')
def get_metrics():
    """Get detailed metrics."""
    return jsonify({
        'current': camera_state['metrics'],
        'history': camera_state['history'][-20:]  # Last 20 entries
    })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start camera monitoring."""
    global monitor_thread, monitoring
    
    if not monitoring:
        monitoring = True
        camera_state['frame_count'] = 0
        camera_state['history'] = []
        monitor_thread = threading.Thread(target=monitor_camera)
        monitor_thread.start()
        return jsonify({'status': 'started'})
    
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop camera monitoring."""
    global monitoring
    
    monitoring = False
    if monitor_thread:
        monitor_thread.join(timeout=2)
    
    return jsonify({'status': 'stopped'})

@app.route('/api/diagnostics')
def run_diagnostics():
    """Run quick diagnostics."""
    cap = cv2.VideoCapture(camera_state['camera_index'])
    
    diagnostics = {
        'camera_available': cap.isOpened(),
        'properties': {},
        'test_capture': False
    }
    
    if cap.isOpened():
        # Get properties
        diagnostics['properties'] = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'backend': cap.getBackendName()
        }
        
        # Test capture
        ret, frame = cap.read()
        diagnostics['test_capture'] = ret
        
        if ret and frame is not None:
            diagnostics['frame_info'] = {
                'shape': frame.shape,
                'mean_brightness': round(np.mean(frame), 2),
                'is_color': len(frame.shape) == 3
            }
    
    cap.release()
    return jsonify(diagnostics)

def generate_frames():
    """
    Generate frames for video streaming using shared camera buffer.
    
    Reads frames from the shared buffer populated by monitor_camera() thread
    instead of opening a separate VideoCapture instance, preventing resource conflicts.
    """
    
    while True:
        # Check if monitoring is active and frames are available
        if not monitoring:
            # If monitoring stopped, show placeholder frame
            placeholder_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder_frame, "Start Monitoring to View Feed", 
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
        with camera_state['frame_lock']:
            if camera_state['current_frame'] is not None:
                frame = camera_state['current_frame'].copy()
        
        if frame is None:
            # No frame available yet, wait briefly
            time.sleep(0.1)
            continue
        
        # Check if frame is too dark and enhance it
        mean_brightness = np.mean(frame)
        if mean_brightness < 50:  # Very dark frame
            # Enhance brightness
            frame = cv2.convertScaleAbs(frame, alpha=2.0, beta=30)
            
        # Add timestamp and status overlay
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add status indicator
        status_color = (0, 255, 0) if camera_state['health_status'] == 'healthy' else (0, 255, 255) if camera_state['health_status'] in ['dark', 'slow'] else (0, 0, 255)
        cv2.circle(frame, (620, 20), 10, status_color, -1)
        
        # Add metrics overlay
        if camera_state.get('metrics'):
            metrics = camera_state['metrics']
            y_pos = 60
            cv2.putText(frame, f"FPS: {metrics.get('fps', 0):.1f}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 25
            cv2.putText(frame, f"Brightness: {metrics.get('brightness', 0):.1f}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 25
            cv2.putText(frame, f"Mean: {mean_brightness:.1f}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control streaming frame rate (slightly lower than capture rate)
        time.sleep(0.033)  # ~30 FPS

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Camera Status Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .grid { 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
        }
        .status-healthy { background: #4CAF50; }
        .status-warning { background: #FFC107; }
        .status-error { background: #F44336; }
        .status-unknown { background: #9E9E9E; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            font-weight: bold;
            color: #2196F3;
        }
        .controls {
            text-align: center;
            padding: 20px;
        }
        button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 5px;
            font-size: 16px;
        }
        button:hover { background: #1976D2; }
        button:disabled { 
            background: #ccc;
            cursor: not-allowed;
        }
        .chart {
            height: 200px;
            background: #f9f9f9;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            position: relative;
            overflow: hidden;
        }
        .history-bar {
            display: inline-block;
            width: 15px;
            background: #2196F3;
            margin: 0 1px;
            vertical-align: bottom;
            transition: height 0.3s;
        }
        h1, h2 { margin-bottom: 10px; }
        .status-text {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Camera Status Dashboard</h1>
            <p>Real-time camera health monitoring and diagnostics</p>
        </div>
        
        <div class="controls">
            <button onclick="startMonitoring()">▶️ Start Monitoring</button>
            <button onclick="stopMonitoring()">⏹️ Stop</button>
            <button onclick="runDiagnostics()">🔍 Run Diagnostics</button>
            <button onclick="resetData()">🔄 Reset</button>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>📹 Live Camera Feed</h2>
                <div style="text-align: center; background: #000; border-radius: 10px; padding: 10px; margin-top: 10px; min-height: 400px; display: flex; align-items: center; justify-content: center;">
                    <img id="live-feed" src="/video_feed" style="max-width: 100%; max-height: 380px; border-radius: 5px; display: none;">
                    <div id="feed-placeholder" style="color: #666;">
                        Click "Start Monitoring" to view live feed
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Camera Status</h2>
                <div id="status-indicator"></div>
                <div class="status-text" id="status-text">Unknown</div>
                <div class="timestamp" id="last-update">No data</div>
                
                <div style="margin-top: 20px;">
                    <div class="metric">
                        <span>Camera Index:</span>
                        <span class="metric-value" id="camera-index">0</span>
                    </div>
                    <div class="metric">
                        <span>Active:</span>
                        <span class="metric-value" id="is-active">No</span>
                    </div>
                    <div class="metric">
                        <span>Frame Count:</span>
                        <span class="metric-value" id="frame-count">0</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Current Metrics</h2>
                <div class="metric">
                    <span>Brightness:</span>
                    <span class="metric-value" id="brightness">-</span>
                </div>
                <div class="metric">
                    <span>Contrast:</span>
                    <span class="metric-value" id="contrast">-</span>
                </div>
                <div class="metric">
                    <span>FPS:</span>
                    <span class="metric-value" id="fps">-</span>
                </div>
                <div class="metric">
                    <span>Frame Time:</span>
                    <span class="metric-value" id="frame-time">-</span>
                </div>
                <div class="metric">
                    <span>Resolution:</span>
                    <span class="metric-value" id="resolution">-</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Brightness History</h2>
                <div class="chart" id="brightness-chart">
                    <div style="text-align: center; padding: 80px 0; color: #999;">
                        Start monitoring to see data
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Diagnostics</h2>
                <div id="diagnostics-result" style="font-family: monospace; font-size: 12px; white-space: pre-wrap;">
                    Click "Run Diagnostics" to test camera
                </div>
            </div>
        </div>
    </div>

    <script>
        let updateInterval = null;
        
        function startMonitoring() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Monitoring started:', data);
                    if (!updateInterval) {
                        updateInterval = setInterval(updateStatus, 1000);
                    }
                    // Show live feed
                    document.getElementById('live-feed').style.display = 'block';
                    document.getElementById('feed-placeholder').style.display = 'none';
                });
        }
        
        function stopMonitoring() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Monitoring stopped:', data);
                    if (updateInterval) {
                        clearInterval(updateInterval);
                        updateInterval = null;
                    }
                    // Hide live feed
                    document.getElementById('live-feed').style.display = 'none';
                    document.getElementById('feed-placeholder').style.display = 'block';
                });
        }
        
        function runDiagnostics() {
            fetch('/api/diagnostics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('diagnostics-result').textContent = 
                        JSON.stringify(data, null, 2);
                });
        }
        
        function resetData() {
            document.getElementById('frame-count').textContent = '0';
            document.getElementById('brightness-chart').innerHTML = 
                '<div style="text-align: center; padding: 80px 0; color: #999;">Start monitoring to see data</div>';
        }
        
        function updateStatus() {
            // Get status
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update status indicator
                    const statusClass = 
                        data.health_status === 'healthy' ? 'status-healthy' :
                        data.health_status === 'dark' || data.health_status === 'slow' ? 'status-warning' :
                        data.health_status === 'error' || data.health_status === 'no_frames' ? 'status-error' :
                        'status-unknown';
                    
                    document.getElementById('status-indicator').innerHTML = 
                        `<span class="status-indicator ${statusClass}"></span>`;
                    
                    document.getElementById('status-text').textContent = 
                        data.health_status.replace('_', ' ').toUpperCase();
                    
                    // Update basic info
                    document.getElementById('camera-index').textContent = data.camera_index;
                    document.getElementById('is-active').textContent = data.is_active ? 'Yes' : 'No';
                    document.getElementById('frame-count').textContent = data.frame_count;
                    
                    if (data.last_update !== null) {
                        document.getElementById('last-update').textContent = 
                            `Last update: ${data.last_update.toFixed(1)}s ago`;
                    }
                    
                    // Update metrics
                    if (data.metrics) {
                        document.getElementById('brightness').textContent = data.metrics.brightness || '-';
                        document.getElementById('contrast').textContent = data.metrics.contrast || '-';
                        document.getElementById('fps').textContent = data.metrics.fps || '-';
                        document.getElementById('frame-time').textContent = 
                            data.metrics.avg_frame_time ? data.metrics.avg_frame_time + 'ms' : '-';
                        document.getElementById('resolution').textContent = data.metrics.resolution || '-';
                    }
                });
            
            // Get metrics history
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.history && data.history.length > 0) {
                        // Create brightness chart
                        const chart = document.getElementById('brightness-chart');
                        const maxBrightness = Math.max(...data.history.map(h => h.brightness));
                        
                        let chartHTML = '';
                        data.history.forEach(entry => {
                            const height = (entry.brightness / maxBrightness) * 180;
                            const color = 
                                entry.status === 'healthy' ? '#4CAF50' :
                                entry.status === 'dark' ? '#FFC107' :
                                '#F44336';
                            
                            chartHTML += `<div class="history-bar" style="height: ${height}px; background: ${color};" title="Brightness: ${entry.brightness.toFixed(1)}"></div>`;
                        });
                        
                        chart.innerHTML = chartHTML;
                    }
                });
        }
        
        // Check status on load
        updateStatus();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🎥 Camera Status Dashboard")
    print("=" * 50)
    print("Access dashboard at: http://localhost:5002")
    print("\nFeatures:")
    print("  ✅ Live video feed streaming")
    print("  ✅ Real-time camera status monitoring")
    print("  ✅ Health metrics and diagnostics")
    print("  ✅ Brightness and FPS tracking")
    print("  ✅ Historical data visualization")
    print("  ✅ One-click diagnostics")
    
    app.run(debug=True, host='0.0.0.0', port=5002, threaded=True)