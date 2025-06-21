#!/usr/bin/env python3
"""
Real Fatigue Detection Backend with OpenCV Face Detection
Uses Haar Cascades instead of MediaPipe for broader compatibility
"""

import cv2
import json
import time
import random
import numpy as np
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
    'camera': None,
    'face_cascade': None,
    'eye_cascade': None
}

# Initialize OpenCV cascades
def init_cascades():
    """Initialize OpenCV Haar Cascades for face and eye detection."""
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if face_cascade.empty() or eye_cascade.empty():
            print("⚠️  Warning: Could not load Haar cascades")
            return None, None
            
        return face_cascade, eye_cascade
    except Exception as e:
        print(f"⚠️  Warning: Error loading cascades: {e}")
        return None, None

# Simple fatigue metrics calculation
class SimpleFatigueDetector:
    def __init__(self):
        self.eye_closure_history = []
        self.blink_count = 0
        self.last_blink_time = 0
        self.perclos_window = 60  # 60 seconds for PERCLOS calculation
        
    def update(self, eyes_detected, timestamp):
        """Update fatigue metrics based on eye detection."""
        
        # Estimate eye openness based on eye detection
        eye_openness = 1.0 if eyes_detected >= 2 else (0.5 if eyes_detected == 1 else 0.1)
        
        # Add to history
        self.eye_closure_history.append({
            'timestamp': timestamp,
            'eye_openness': eye_openness,
            'eyes_detected': eyes_detected
        })
        
        # Keep only last 60 seconds
        cutoff_time = timestamp - self.perclos_window
        self.eye_closure_history = [
            entry for entry in self.eye_closure_history 
            if entry['timestamp'] > cutoff_time
        ]
        
        # Calculate PERCLOS (percentage of time eyes are <80% open)
        if len(self.eye_closure_history) > 10:  # Need some data
            closed_samples = sum(1 for entry in self.eye_closure_history if entry['eye_openness'] < 0.8)
            perclos_percentage = (closed_samples / len(self.eye_closure_history)) * 100
        else:
            perclos_percentage = 0
        
        # Detect blinks (transition from open to closed to open)
        if len(self.eye_closure_history) >= 3:
            recent = self.eye_closure_history[-3:]
            if (recent[0]['eye_openness'] > 0.8 and 
                recent[1]['eye_openness'] < 0.3 and 
                recent[2]['eye_openness'] > 0.8):
                if timestamp - self.last_blink_time > 0.2:  # Minimum 200ms between blinks
                    self.blink_count += 1
                    self.last_blink_time = timestamp
        
        # Calculate blink rate per minute
        session_duration = len(self.eye_closure_history) / 30.0  # Assuming 30 fps
        blink_rate = (self.blink_count / max(session_duration, 1)) * 60 if session_duration > 0 else 0
        
        # Determine fatigue level
        if perclos_percentage < 15:
            fatigue_level = 'alert'
        elif perclos_percentage < 40:
            fatigue_level = 'warning'
        else:
            fatigue_level = 'critical'
        
        return {
            'perclos_percentage': perclos_percentage,
            'fatigue_level': fatigue_level,
            'eye_openness': eye_openness,
            'blink_rate': blink_rate,
            'blink_count': self.blink_count,
            'eyes_detected': eyes_detected
        }

# Initialize components
demo_state['face_cascade'], demo_state['eye_cascade'] = init_cascades()
fatigue_detector = SimpleFatigueDetector()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start webcam detection."""
    global demo_state, fatigue_detector
    
    try:
        # Initialize webcam
        demo_state['camera'] = cv2.VideoCapture(0)
        
        if not demo_state['camera'].isOpened():
            return jsonify({'status': 'error', 'message': 'Cannot access webcam'})
        
        # Set camera properties
        demo_state['camera'].set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        demo_state['camera'].set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        demo_state['camera'].set(cv2.CAP_PROP_FPS, 30)
        
        demo_state['running'] = True
        demo_state['session_start_time'] = time.time()
        demo_state['frame_count'] = 0
        demo_state['perclos_history'] = []
        demo_state['blink_history'] = []
        
        # Reset detector
        fatigue_detector = SimpleFatigueDetector()
        
        return jsonify({'status': 'success', 'message': 'Webcam detection started'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error starting detection: {str(e)}'})

@app.route('/stop_detection', methods=['POST'])  
def stop_detection():
    """Stop webcam detection."""
    global demo_state
    
    demo_state['running'] = False
    
    if demo_state['camera']:
        demo_state['camera'].release()
        demo_state['camera'] = None
    
    return jsonify({'status': 'success', 'message': 'Detection stopped'})

@app.route('/reset_metrics', methods=['POST'])
def reset_metrics():
    """Reset all metrics."""
    global demo_state, fatigue_detector
    demo_state['current_metrics'] = {}
    demo_state['alert_status'] = {}
    demo_state['perclos_history'] = []
    demo_state['blink_history'] = []
    demo_state['frame_count'] = 0
    demo_state['session_start_time'] = time.time() if demo_state['running'] else None
    fatigue_detector = SimpleFatigueDetector()
    return jsonify({'status': 'success', 'message': 'Metrics reset'})

@app.route('/get_metrics')
def get_metrics_frontend():
    """Get current metrics for frontend."""
    
    if demo_state['running'] and demo_state['camera']:
        # Process one frame for real-time metrics
        success, frame = demo_state['camera'].read()
        
        if success:
            demo_state['frame_count'] += 1
            
            # Detect faces and eyes
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = []
            eyes_detected = 0
            
            if demo_state['face_cascade'] is not None:
                faces = demo_state['face_cascade'].detectMultiScale(gray, 1.3, 5)
                
                # For each face, detect eyes
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]
                    if demo_state['eye_cascade'] is not None:
                        eyes = demo_state['eye_cascade'].detectMultiScale(roi_gray)
                        eyes_detected = len(eyes)
                        break  # Use first face only
            
            # Update fatigue metrics
            timestamp = time.time()
            metrics = fatigue_detector.update(eyes_detected, timestamp)
            
            # Determine alert status
            perclos = metrics['perclos_percentage']
            if perclos < 20:
                alert_level = 'Normal'
                alert_message = 'All systems normal'
            elif perclos < 50:
                alert_level = 'Warning' 
                alert_message = f'Mild fatigue detected (PERCLOS: {perclos:.1f}%) - consider taking a break'
            else:
                alert_level = 'Critical'
                alert_message = f'High fatigue detected (PERCLOS: {perclos:.1f}%) - immediate break recommended'
            
            response = {
                'metrics': {
                    'perclos': perclos / 100.0,  # Convert to 0-1 range
                    'blink_rate': metrics['blink_rate'],
                    'eye_openness': metrics['eye_openness'],
                },
                'alert_status': {
                    'level': alert_level,
                    'message': alert_message
                },
                'frame_count': demo_state['frame_count'],
                'fps': 30.0,
                'faces_detected': len(faces),
                'eyes_detected': eyes_detected
            }
            
            # Store for history
            demo_state['current_metrics'] = response['metrics']
            demo_state['alert_status'] = response['alert_status']
        
        else:
            response = {
                'metrics': {'perclos': 0.0, 'blink_rate': 0.0, 'eye_openness': 1.0},
                'alert_status': {'level': 'Normal', 'message': 'Camera error'},
                'frame_count': demo_state['frame_count'],
                'fps': 0.0,
                'faces_detected': 0,
                'eyes_detected': 0
            }
    
    else:
        # System not running
        response = {
            'metrics': {'perclos': 0.0, 'blink_rate': 0.0, 'eye_openness': 1.0},
            'alert_status': {'level': 'Normal', 'message': 'System not running'},
            'frame_count': demo_state.get('frame_count', 0),
            'fps': 0.0,
            'faces_detected': 0,
            'eyes_detected': 0
        }
    
    return jsonify(response)

@app.route('/video_feed')
def video_feed():
    """Live video feed with face detection overlay."""
    return Response(generate_video_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_video_frames():
    """Generate video frames with face and eye detection overlay."""
    while demo_state['running'] and demo_state['camera']:
        success, frame = demo_state['camera'].read()
        
        if not success:
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = []
        if demo_state['face_cascade'] is not None:
            faces = demo_state['face_cascade'].detectMultiScale(gray, 1.3, 5)
        
        total_eyes = 0
        
        # Draw face rectangles and detect eyes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Detect eyes in face region
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            if demo_state['eye_cascade'] is not None:
                eyes = demo_state['eye_cascade'].detectMultiScale(roi_gray)
                total_eyes += len(eyes)
                
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
                    cv2.putText(roi_color, 'Eye', (ex, ey-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Draw status overlay
        status_text = f"Faces: {len(faces)} | Eyes: {total_eyes}"
        cv2.rectangle(frame, (10, 10), (300, 60), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add metrics overlay if available
        if demo_state.get('current_metrics'):
            metrics = demo_state['current_metrics']
            alert = demo_state.get('alert_status', {})
            
            perclos_text = f"PERCLOS: {metrics.get('perclos', 0)*100:.1f}%"
            blink_text = f"Blinks: {metrics.get('blink_rate', 0):.1f}/min"
            alert_text = f"Alert: {alert.get('level', 'Normal')}"
            
            cv2.putText(frame, perclos_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, blink_text, (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Color-code alert level
            alert_color = (0, 255, 0) if alert.get('level') == 'Normal' else (0, 255, 255) if alert.get('level') == 'Warning' else (0, 0, 255)
            cv2.putText(frame, alert_text, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, alert_color, 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/status')
def status():
    """System status endpoint."""
    cascade_status = "Available" if demo_state['face_cascade'] is not None else "Not Available"
    
    return jsonify({
        'status': 'running' if demo_state['running'] else 'stopped',
        'timestamp': datetime.now().isoformat(),
        'system': 'Real Fatigue Detection System with OpenCV',
        'face_detection': cascade_status,
        'webcam_access': demo_state['camera'] is not None,
        'features': [
            'Real webcam processing',
            'OpenCV face detection',
            'Eye detection and tracking',
            'Real-time PERCLOS calculation',
            'Blink rate monitoring',
            'Progressive alert system'
        ]
    })

# Update dashboard template to include video feed
@app.route('/dashboard_with_video')
def dashboard_with_video():
    """Dashboard with live video feed."""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real Fatigue Detection Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; color: #333; margin-bottom: 20px; }
            .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .panel { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .video-feed { width: 100%; max-width: 640px; border: 2px solid #ddd; border-radius: 5px; }
            .controls { text-align: center; margin: 20px 0; }
            button { padding: 10px 20px; margin: 0 10px; border: none; border-radius: 5px; cursor: pointer; }
            .start-btn { background: #28a745; color: white; }
            .stop-btn { background: #dc3545; color: white; }
            .metric { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
            .status { padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; font-weight: bold; }
            .status.normal { background: #d1fae5; color: #065f46; }
            .status.warning { background: #fef3c7; color: #92400e; }
            .status.critical { background: #fecaca; color: #991b1b; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎥 Real Fatigue Detection System</h1>
                <p>OpenCV-powered face detection with webcam integration</p>
            </div>
            
            <div class="controls">
                <button class="start-btn" onclick="startDetection()">🎥 Start Webcam</button>
                <button class="stop-btn" onclick="stopDetection()">⏹️ Stop</button>
                <button onclick="resetMetrics()">🔄 Reset</button>
            </div>
            
            <div id="status" class="status normal">Ready - Click Start Webcam to begin</div>
            
            <div class="dashboard">
                <div class="panel">
                    <h3>Live Video Feed</h3>
                    <img class="video-feed" id="videoFeed" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPldlYmNhbSBGZWVkPC90ZXh0Pjwvc3ZnPg==" alt="Webcam Feed">
                </div>
                
                <div class="panel">
                    <h3>Real-time Metrics</h3>
                    <div class="metric">
                        <strong>PERCLOS:</strong> <span id="perclos">0.0%</span>
                    </div>
                    <div class="metric">
                        <strong>Blink Rate:</strong> <span id="blink-rate">0.0/min</span>
                    </div>
                    <div class="metric">
                        <strong>Eye Openness:</strong> <span id="eye-openness">100%</span>
                    </div>
                    <div class="metric">
                        <strong>Faces Detected:</strong> <span id="faces">0</span>
                    </div>
                    <div class="metric">
                        <strong>Eyes Detected:</strong> <span id="eyes">0</span>
                    </div>
                    <div class="metric">
                        <strong>Frame Count:</strong> <span id="frames">0</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let isRunning = false;
            let updateInterval = null;
            
            function startDetection() {
                fetch('/start_detection', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            isRunning = true;
                            document.getElementById('status').textContent = 'Webcam Active - Processing video feed...';
                            document.getElementById('status').className = 'status normal';
                            document.getElementById('videoFeed').src = '/video_feed?' + Date.now();
                            updateInterval = setInterval(updateMetrics, 1000);
                        } else {
                            alert('Error: ' + data.message);
                        }
                    });
            }
            
            function stopDetection() {
                fetch('/stop_detection', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        isRunning = false;
                        document.getElementById('status').textContent = 'Stopped - Click Start Webcam to resume';
                        document.getElementById('status').className = 'status normal';
                        document.getElementById('videoFeed').src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPldlYmNhbSBGZWVkPC90ZXh0Pjwvc3ZnPg==';
                        if (updateInterval) clearInterval(updateInterval);
                    });
            }
            
            function resetMetrics() {
                fetch('/reset_metrics', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('perclos').textContent = '0.0%';
                        document.getElementById('blink-rate').textContent = '0.0/min';
                        document.getElementById('eye-openness').textContent = '100%';
                        document.getElementById('faces').textContent = '0';
                        document.getElementById('eyes').textContent = '0';
                        document.getElementById('frames').textContent = '0';
                    });
            }
            
            function updateMetrics() {
                if (!isRunning) return;
                
                fetch('/get_metrics')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('perclos').textContent = (data.metrics.perclos * 100).toFixed(1) + '%';
                        document.getElementById('blink-rate').textContent = data.metrics.blink_rate.toFixed(1) + '/min';
                        document.getElementById('eye-openness').textContent = (data.metrics.eye_openness * 100).toFixed(0) + '%';
                        document.getElementById('faces').textContent = data.faces_detected || 0;
                        document.getElementById('eyes').textContent = data.eyes_detected || 0;
                        document.getElementById('frames').textContent = data.frame_count || 0;
                        
                        // Update status based on alert level
                        const alert = data.alert_status;
                        const statusElement = document.getElementById('status');
                        statusElement.textContent = alert.message;
                        
                        if (alert.level === 'Critical') {
                            statusElement.className = 'status critical';
                        } else if (alert.level === 'Warning') {
                            statusElement.className = 'status warning';
                        } else {
                            statusElement.className = 'status normal';
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
        </script>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    print("🎥 Starting REAL Fatigue Detection Backend with OpenCV...")
    print("📊 Features:")
    print("  ✅ Real webcam processing")
    print("  ✅ OpenCV face detection")
    print("  ✅ Eye detection and tracking") 
    print("  ✅ Real-time PERCLOS calculation")
    print("  ✅ Blink rate monitoring")
    print("  ✅ Progressive alert system")
    print("  ✅ Live video feed with overlays")
    print("\n🌐 Access dashboard at: http://localhost:5001")
    print("🎬 Video dashboard at: http://localhost:5001/dashboard_with_video")
    
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)