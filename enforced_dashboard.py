#!/usr/bin/env python3
"""
Enforced Dashboard - Fatigue Detection with Core Pipeline

This dashboard uses the core pipeline with enforced foundation validation.
No functionality works without proper layer validation.
"""

from flask import Flask, render_template_string, jsonify, Response
import cv2
import time
import numpy as np
from datetime import datetime

# Import core pipeline
from core_pipeline import pipeline, get_pipeline

app = Flask(__name__)

# Dashboard state
dashboard_state = {
    'pipeline_started': False,
    'start_time': None,
    'frame_count': 0
}


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/validate_stack', methods=['POST'])
def validate_stack():
    """Validate entire stack using core pipeline."""
    try:
        # Validate up to analysis layer
        success = pipeline.validate_stack('analysis')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All validations passed',
                'status': pipeline.get_validation_status()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'status': pipeline.get_validation_status()
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/start_pipeline', methods=['POST'])
def start_pipeline():
    """Start the full pipeline."""
    try:
        # Check if already started
        if dashboard_state['pipeline_started']:
            return jsonify({
                'success': True,
                'message': 'Pipeline already running'
            })
        
        # Initialize all components (enforced validation)
        pipeline.initialize_camera()
        pipeline.start_health_monitoring()
        pipeline.start_video_streaming()
        pipeline.start_fatigue_analysis()
        
        dashboard_state['pipeline_started'] = True
        dashboard_state['start_time'] = time.time()
        
        return jsonify({
            'success': True,
            'message': 'Pipeline started successfully'
        })
        
    except RuntimeError as e:
        # Foundation enforcement errors
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'validation_error'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'general_error'
        })


@app.route('/api/stop_pipeline', methods=['POST'])
def stop_pipeline():
    """Stop the pipeline."""
    try:
        pipeline.shutdown()
        dashboard_state['pipeline_started'] = False
        
        return jsonify({
            'success': True,
            'message': 'Pipeline stopped'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/status')
def get_status():
    """Get comprehensive system status."""
    try:
        validation_status = pipeline.get_validation_status()
        metrics = pipeline.get_metrics()
        
        # Add dashboard info
        uptime = 0
        if dashboard_state['pipeline_started'] and dashboard_state['start_time']:
            uptime = round(time.time() - dashboard_state['start_time'], 1)
        
        return jsonify({
            'pipeline_active': dashboard_state['pipeline_started'],
            'uptime_seconds': uptime,
            'validation': validation_status,
            'metrics': metrics
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        })


@app.route('/api/metrics/<layer>')
def get_layer_metrics(layer):
    """Get metrics for specific layer."""
    try:
        metrics = pipeline.get_metrics(layer)
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        })


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    def generate():
        while True:
            try:
                # This will fail if streaming not validated
                frame = pipeline.get_frame(annotated=True)
                
                if frame is None:
                    # No frame available, show placeholder
                    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(placeholder, "Waiting for video stream...", 
                               (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    _, buffer = cv2.imencode('.jpg', placeholder)
                    frame = buffer.tobytes()
                else:
                    # Add fatigue metrics if available
                    if dashboard_state['pipeline_started']:
                        analysis_metrics = pipeline.get_metrics('analysis')
                        
                        if analysis_metrics:
                            perclos = analysis_metrics.get('perclos', 0)
                            alert = analysis_metrics.get('alert_level', 'none')
                            
                            # Add to frame
                            cv2.putText(frame, f"PERCLOS: {perclos:.1f}%", 
                                       (frame.shape[1] - 200, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            
                            if alert != 'none':
                                color = (0, 255, 255) if alert == 'warning' else (0, 0, 255)
                                cv2.putText(frame, f"ALERT: {alert.upper()}", 
                                           (frame.shape[1] - 200, 60),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                       
            except RuntimeError:
                # Not validated, show error
                error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(error_frame, "Video stream not validated", 
                           (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                _, buffer = cv2.imencode('.jpg', error_frame)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            except Exception as e:
                print(f"Video feed error: {e}")
            
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Enforced Dashboard - Core Pipeline</title>
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
        .validation-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        .validation-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .validation-card.passed {
            background: #E8F5E9;
            border: 2px solid #4CAF50;
        }
        .validation-card.failed {
            background: #FFEBEE;
            border: 2px solid #F44336;
        }
        .validation-card.expired {
            background: #FFF3E0;
            border: 2px solid #FF9800;
        }
        .layer-name {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 10px;
        }
        .layer-status {
            font-size: 14px;
            color: #666;
        }
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        button {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background-color: #1976D2; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        .validate-btn { background-color: #FF5722; }
        .validate-btn:hover { background-color: #E64A19; }
        .start-btn { background-color: #4CAF50; }
        .start-btn:hover { background-color: #45a049; }
        .stop-btn { background-color: #F44336; }
        .stop-btn:hover { background-color: #E53935; }
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
        .metric-group {
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .metric-group h3 {
            margin-top: 0;
            color: #333;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
        }
        .metric-label {
            color: #666;
        }
        .metric-value {
            font-weight: bold;
            color: #333;
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
        .enforcement-notice {
            background: #E3F2FD;
            border: 2px solid #2196F3;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ Enforced Dashboard - Core Pipeline</h1>
        <p>Foundation-First Architecture with Strict Validation</p>
    </div>
    
    <div class="enforcement-notice">
        <strong>⚡ Foundation Enforcement Active</strong><br>
        Higher functions cannot execute without lower layer validation
    </div>
    
    <div class="validation-grid" id="validation-grid">
        <div class="validation-card" id="foundation-card">
            <div class="layer-name">🎯 Foundation</div>
            <div class="layer-status">Not Validated</div>
        </div>
        <div class="validation-card" id="health-card">
            <div class="layer-name">📊 Health</div>
            <div class="layer-status">Not Validated</div>
        </div>
        <div class="validation-card" id="streaming-card">
            <div class="layer-name">📹 Streaming</div>
            <div class="layer-status">Not Validated</div>
        </div>
        <div class="validation-card" id="analysis-card">
            <div class="layer-name">🧠 Analysis</div>
            <div class="layer-status">Not Validated</div>
        </div>
    </div>
    
    <div id="status-message" class="status-message" style="display:none;"></div>
    
    <div class="controls">
        <button onclick="validateStack()" class="validate-btn">🔍 Validate Stack</button>
        <button onclick="startPipeline()" id="start-btn" disabled class="start-btn">▶️ Start Pipeline</button>
        <button onclick="stopPipeline()" id="stop-btn" disabled class="stop-btn">⏹️ Stop Pipeline</button>
    </div>
    
    <div class="main-content">
        <div class="video-container">
            <h2>📹 Live Video Feed</h2>
            <img id="video-feed" src="/video_feed" style="display:block;">
        </div>
        
        <div class="metrics-container">
            <h2>📊 System Metrics</h2>
            
            <div class="metric-group">
                <h3>🎥 Camera</h3>
                <div id="camera-metrics">
                    <div class="metric">
                        <span class="metric-label">Status</span>
                        <span class="metric-value">--</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-group">
                <h3>📊 Health</h3>
                <div id="health-metrics">
                    <div class="metric">
                        <span class="metric-label">FPS</span>
                        <span class="metric-value">--</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-group">
                <h3>🧠 Analysis</h3>
                <div id="analysis-metrics">
                    <div class="metric">
                        <span class="metric-label">PERCLOS</span>
                        <span class="metric-value">--</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        
        function updateValidationDisplay(validation) {
            const layers = ['foundation', 'health', 'streaming', 'analysis'];
            
            layers.forEach(layer => {
                const card = document.getElementById(`${layer}-card`);
                const status = validation[layer];
                
                if (!status) return;
                
                // Update card style
                card.className = 'validation-card';
                if (status.valid) {
                    card.classList.add('passed');
                } else if (status.status === 'expired') {
                    card.classList.add('expired');
                } else if (status.status === 'failed') {
                    card.classList.add('failed');
                }
                
                // Update status text
                const statusEl = card.querySelector('.layer-status');
                let statusText = status.status.replace('_', ' ').toUpperCase();
                
                if (status.expires_in) {
                    statusText += ` (${Math.round(status.expires_in)}s)`;
                }
                
                statusEl.textContent = statusText;
            });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status-message');
            statusDiv.textContent = message;
            statusDiv.className = 'status-message status-' + (type === 'error' ? 'error' : 'success');
            statusDiv.style.display = 'block';
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
        function validateStack() {
            showStatus('Validating stack...', 'info');
            
            fetch('/api/validate_stack', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateValidationDisplay(data.status);
                    
                    if (data.success) {
                        showStatus('✅ All validations passed!', 'success');
                        document.getElementById('start-btn').disabled = false;
                    } else {
                        showStatus('❌ Validation failed. Check requirements.', 'error');
                        document.getElementById('start-btn').disabled = true;
                    }
                });
        }
        
        function startPipeline() {
            fetch('/api/start_pipeline', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('Pipeline started successfully', 'success');
                        document.getElementById('start-btn').disabled = true;
                        document.getElementById('stop-btn').disabled = false;
                        startUpdating();
                    } else {
                        if (data.type === 'validation_error') {
                            showStatus('❌ ' + data.error, 'error');
                        } else {
                            showStatus('Failed to start: ' + data.error, 'error');
                        }
                    }
                });
        }
        
        function stopPipeline() {
            fetch('/api/stop_pipeline', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showStatus('Pipeline stopped', 'info');
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    stopUpdating();
                });
        }
        
        function updateMetrics() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update validation display
                    if (data.validation) {
                        updateValidationDisplay(data.validation);
                    }
                    
                    // Update metrics
                    if (data.metrics) {
                        // Camera metrics
                        const cameraDiv = document.getElementById('camera-metrics');
                        if (data.metrics.camera && data.metrics.camera.resolution) {
                            cameraDiv.innerHTML = `
                                <div class="metric">
                                    <span class="metric-label">Resolution</span>
                                    <span class="metric-value">${data.metrics.camera.resolution}</span>
                                </div>
                            `;
                        }
                        
                        // Health metrics
                        const healthDiv = document.getElementById('health-metrics');
                        if (data.metrics.health && data.metrics.health.fps) {
                            healthDiv.innerHTML = `
                                <div class="metric">
                                    <span class="metric-label">FPS</span>
                                    <span class="metric-value">${data.metrics.health.fps}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Brightness</span>
                                    <span class="metric-value">${data.metrics.health.brightness || '--'}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Status</span>
                                    <span class="metric-value">${data.metrics.health.health_status || '--'}</span>
                                </div>
                            `;
                        }
                        
                        // Analysis metrics
                        const analysisDiv = document.getElementById('analysis-metrics');
                        if (data.metrics.analysis && data.metrics.analysis.perclos !== undefined) {
                            analysisDiv.innerHTML = `
                                <div class="metric">
                                    <span class="metric-label">PERCLOS</span>
                                    <span class="metric-value">${data.metrics.analysis.perclos.toFixed(1)}%</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Fatigue Level</span>
                                    <span class="metric-value">${data.metrics.analysis.fatigue_level || '--'}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Alert</span>
                                    <span class="metric-value">${data.metrics.analysis.alert_level || 'none'}</span>
                                </div>
                            `;
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
        
        // Initial update
        updateMetrics();
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("🏗️ ENFORCED DASHBOARD - CORE PIPELINE")
    print("=" * 50)
    print("Foundation-first architecture with strict validation")
    print("Higher functions require lower layer validation")
    print("\nAccess dashboard at: http://localhost:5000")
    print("\n⚡ ENFORCEMENT ACTIVE:")
    print("  - Camera operations require foundation validation")
    print("  - Monitoring requires health validation")
    print("  - Streaming requires monitoring active")
    print("  - Analysis requires entire stack validated")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)