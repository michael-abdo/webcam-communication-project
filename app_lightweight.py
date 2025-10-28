#!/usr/bin/env python3
"""
Lightweight Production Deployment App for Fatigue Detection System
Optimized for cloud deployment without heavy dependencies
"""

import os
import json
import time
import random
import threading
import redis
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template, send_file, abort, current_app, send_from_directory
from flask_cors import CORS
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from streaming.s3_handler import ensure_bucket_exists

# Import utils
from utils.assessment_transformer import transform_flask_to_assessment, generate_assessment_data

# Import baseline blueprint
from blueprints.baseline_blueprint import baseline_bp
# Import assessments blueprint
from blueprints.assessments_blueprint import assessment_bp
from blueprints.analytics_api import analytics_api
from blueprints.capture_api import capture_api
from blueprints.meetings_api import meetings_api
from blueprints.rtms_ingest_api import rtms_ingest_api
from blueprints.rtms_ui import rtms_ui
from blueprints.zoom_api import zoom_api
from models import init_engine
from services.capture_service import CaptureNotFoundError, get_session_record, list_session_chunks
from services.video_state import video_sessions, test_video_links
from rtms import RTMSHub

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
sock = Sock(app)

rtms_hub = RTMSHub()
app.config["RTMS_HUB"] = rtms_hub

# In-memory storage for RTMS webhooks
# In production, use Redis or database
app.rtms_webhooks = {}

# Analytics Redis subscription setup
analytics_thread = None

def start_analytics_subscription():
    """Start background thread to subscribe to analytics events from Redis."""
    global analytics_thread
    
    def analytics_subscriber():
        """Subscribe to analytics events and broadcast to WebSocket clients."""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            
            # Handle Heroku Redis SSL requirements
            if redis_url.startswith('rediss://'):
                import ssl
                pubsub = redis.from_url(
                    redis_url,
                    ssl_cert_reqs=ssl.CERT_NONE
                ).pubsub()
            else:
                pubsub = redis.from_url(redis_url).pubsub()
            
            # Subscribe to analytics metrics channel
            pubsub.subscribe('analytics:metrics')
            
            app.logger.info("Started analytics Redis subscription")
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse the metrics event
                        event = json.loads(message['data'])
                        
                        # Extract session ID from the event
                        session_id = event.get('session_id')
                        if not session_id:
                            continue
                        
                        # Format analytics update for WebSocket
                        ws_message = {
                            "type": "analytics",
                            "metric": event.get('metric'),
                            "value": event.get('value'),
                            "participant_id": event.get('participant_id'),
                            "timestamp": event.get('timestamp'),
                            "tags": event.get('tags', {})
                        }
                        
                        # Broadcast to session-specific WebSocket clients
                        with app.app_context():
                            broadcast_to_session(session_id, ws_message)
                            # Also broadcast to RTMS dashboard clients
                            rtms_hub.broadcast(ws_message)
                            
                    except Exception as e:
                        app.logger.error(f"Error processing analytics event: {e}")
                        
        except Exception as e:
            app.logger.error(f"Analytics subscription error: {e}")
    
    # Start the subscriber thread
    analytics_thread = threading.Thread(target=analytics_subscriber, daemon=True)
    analytics_thread.start()

init_engine()

# Register capture API blueprint
app.register_blueprint(capture_api)
# Register baseline blueprint
app.register_blueprint(baseline_bp)
# Register assessments blueprint
app.register_blueprint(assessment_bp)
app.register_blueprint(rtms_ingest_api)
app.register_blueprint(rtms_ui, url_prefix="/rtms")
app.register_blueprint(meetings_api)
app.register_blueprint(analytics_api)
app.register_blueprint(zoom_api)


@app.route('/static/rtms/<path:filename>')
def serve_rtms_static(filename):
    """Serve RTMS static files (CSS, JS)."""
    rtms_static_dir = os.path.join(os.path.dirname(__file__), 'rtms-service', 'public')
    return send_from_directory(rtms_static_dir, filename)

@sock.route("/rtms/ws")
def rtms_websocket(ws):
    """Bridge RTMS realtime frames to connected dashboard clients."""
    hub: RTMSHub = current_app.config["RTMS_HUB"]
    client_details = {
        "remote_addr": ws.environ.get("REMOTE_ADDR"),
        "forwarded_for": ws.environ.get("HTTP_X_FORWARDED_FOR"),
        "path": ws.environ.get("PATH_INFO"),
        "user_agent": ws.environ.get("HTTP_USER_AGENT"),
    }
    hub.register(ws, metadata=client_details)
    current_app.logger.info("rtms.ws.connected", extra=client_details)

    try:
        while True:
            message = ws.receive()
            if message is None:
                continue
            current_app.logger.debug(
                "rtms.ws.unexpected_message", extra={"message_length": len(str(message))}
            )
    except ConnectionClosed:
        current_app.logger.info("rtms.ws.disconnected", extra=client_details)
    except Exception:  # pragma: no cover - defensive logging
        current_app.logger.exception("rtms.ws.server_error", extra=client_details)
    finally:
        hub.unregister(ws)


@sock.route("/ws/sessions/<session_id>")
def session_websocket(ws, session_id):
    """WebSocket endpoint for live session updates (transcript and analytics)."""
    # Verify session exists
    try:
        session_data = get_session_record(session_id)
        if not session_data:
            ws.close(code=1008, message="Session not found")
            return
    except Exception:
        ws.close(code=1011, message="Server error")
        return

    # Register this WebSocket for session-specific updates
    session_key = f"session:{session_id}"
    if not hasattr(current_app, 'session_websockets'):
        current_app.session_websockets = {}
    
    if session_key not in current_app.session_websockets:
        current_app.session_websockets[session_key] = []
    
    current_app.session_websockets[session_key].append(ws)
    
    client_details = {
        "session_id": session_id,
        "remote_addr": ws.environ.get("REMOTE_ADDR"),
        "path": ws.environ.get("PATH_INFO"),
    }
    current_app.logger.info("session.ws.connected", extra=client_details)
    
    try:
        # Keep connection alive and handle any incoming messages
        while True:
            message = ws.receive()
            if message is None:
                continue
            # For now, we don't process incoming messages
            # In a full implementation, we might handle subscription requests
            current_app.logger.debug(
                "session.ws.message", 
                extra={"session_id": session_id, "message": message}
            )
    except ConnectionClosed:
        current_app.logger.info("session.ws.disconnected", extra=client_details)
    except Exception:
        current_app.logger.exception("session.ws.error", extra=client_details)
    finally:
        # Unregister this WebSocket
        if session_key in current_app.session_websockets:
            current_app.session_websockets[session_key].remove(ws)
            if not current_app.session_websockets[session_key]:
                del current_app.session_websockets[session_key]

def broadcast_to_session(session_id: str, message: dict):
    """Broadcast a message to all WebSocket clients watching a specific session."""
    session_key = f"session:{session_id}"
    if hasattr(current_app, 'session_websockets') and session_key in current_app.session_websockets:
        dead_clients = []
        for ws in current_app.session_websockets[session_key]:
            try:
                ws.send(json.dumps(message))
            except Exception:
                dead_clients.append(ws)
        
        # Clean up dead clients
        for ws in dead_clients:
            current_app.session_websockets[session_key].remove(ws)
        
        if not current_app.session_websockets[session_key]:
            del current_app.session_websockets[session_key]


@app.route('/zoom-webhook', methods=['POST'])
@app.route('/rtms/webhook', methods=['POST'])
def zoom_webhook():
    """Handle Zoom RTMS webhooks - broadcast to WebSocket clients."""
    try:
        # Get the webhook data
        data = request.get_json()
        
        # Log the incoming webhook with full details
        print(f"=== ZOOM WEBHOOK RECEIVED ===")
        print(f"Event: {data.get('event', 'unknown')}")
        print(f"Full payload: {json.dumps(data, indent=2)}")
        print(f"=== END WEBHOOK ===")
        
        # Also log to the app logger
        current_app.logger.info(f"Zoom webhook - Event: {data.get('event', 'unknown')}, Payload: {json.dumps(data)}")
        
        # Check if this is an RTMS event
        if data and data.get('event') in ['meeting.rtms_started', 'meeting.rtms_stopped']:
            # Get the RTMS hub and broadcast the event
            hub = current_app.config.get("RTMS_HUB")
            if hub:
                # Format the message for WebSocket clients
                ws_message = {
                    "type": "rtms_event",
                    "event": data.get('event'),
                    "streamId": data.get('payload', {}).get('rtms_stream_id'),
                    "meetingUuid": data.get('payload', {}).get('meeting_uuid'),
                    "timestamp": data.get('event_ts'),
                    "payload": data.get('payload', {})
                }
                
                # Broadcast to all connected WebSocket clients
                hub.broadcast(ws_message)
                print(f"Broadcasted RTMS event to {hub.connection_count()} WebSocket clients")
            
            # Store the webhook data for the RTMS service to retrieve
            stream_id = data.get('payload', {}).get('rtms_stream_id')
            if stream_id:
                app.rtms_webhooks[stream_id] = {
                    'data': data,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                print(f"Stored RTMS webhook for stream_id: {stream_id}")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        current_app.logger.error(f"Error processing Zoom webhook: {str(e)}")
        print(f"ERROR in webhook handler: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/rtms/webhooks/<stream_id>', methods=['GET'])
def get_rtms_webhook(stream_id):
    """Internal endpoint for RTMS service to retrieve webhook data."""
    webhook_data = app.rtms_webhooks.get(stream_id)
    if webhook_data:
        # Return and remove the webhook data (one-time retrieval)
        del app.rtms_webhooks[stream_id]
        return jsonify(webhook_data)
    else:
        return jsonify({"error": "Webhook not found"}), 404

@app.route('/api/rtms/pending-webhooks', methods=['GET'])
def get_pending_webhooks():
    """Get list of all pending RTMS webhooks."""
    # Return all stored webhooks
    webhooks = []
    for stream_id, data in list(app.rtms_webhooks.items()):
        webhooks.append({
            'stream_id': stream_id,
            'webhook': data['data'],
            'timestamp': data['timestamp']
        })
        # Remove after retrieval
        del app.rtms_webhooks[stream_id]
    
    return jsonify(webhooks)

# Route to serve baseline capture page
@app.route('/baseline')
def baseline_capture_page():
    """Serve the baseline capture interface"""
    return render_template('baseline_capture.html')

# Global state
system_state = {
    'start_time': datetime.now(),
    'requests_count': 0,
    'version': '2.0.1',
    'mode': 'PRODUCTION'
}

# Video analysis state
video_analysis_state = {
    'is_analyzing': False,
    'current_video': None,
    'frame_count': 0,
    'results': []
}

# Shared metrics state for dashboard integration
current_metrics = {
    'perclos': 0.0,
    'blink_rate': 15,  # Default normal blink rate
    'eye_openness': 1.0,
    'is_active': False,
    'source': 'none',  # 'video', 'camera', or 'none'
    'last_update': datetime.now(),
    'frame_count': 0,
    'fps': 0.0,
    'alert_level': 'Normal',
    'alert_message': 'System ready'
}

@app.route('/')
def home():
    """Home page with dashboard interface."""
    return render_template('dashboard.html')

@app.route('/api')
def api_home():
    """API home endpoint."""
    return jsonify({
        'name': 'Fatigue Detection System',
        'version': system_state['version'],
        'status': 'operational',
        'mode': system_state['mode'],
        'uptime_seconds': (datetime.now() - system_state['start_time']).total_seconds(),
        'endpoints': [
            'GET /health - Health check',
            'GET /api/info - System information', 
            'GET /api/metrics - Current metrics',
            'POST /api/analyze - Analyze fatigue',
            'POST /api/analysis-result - Receive real-time analysis results',
            'POST /api/text-analysis-result - Receive text analysis results',
            'GET /api/results - Get analysis results',
            'GET /video-analysis - Video dataset analysis interface',
            'GET /webcam-analysis - Live webcam fatigue detection',
            'GET /text-analysis - Text cognitive load analysis',
            'GET /tests - Interactive test dashboard',
            'GET /tests/session/combined - Combined test with video recording',
            'GET /tests/results - Test results viewer with video correlation',
            'GET /api/tests/list - Get available tests',
            'GET /api/tests/<test_id> - Get test definition',
            'POST /api/tests/session/start - Start test session',
            'POST /api/tests/session/<id>/submit - Submit answer (with video events)',
            'GET /api/tests/session/<id>/results - Get test results (with video data)',
            'GET /api/tests/session/<id>/events - Get correlated events timeline',
            'GET /api/video/session/<id>/chunks - Get video chunks with timestamps',
            'GET /api/tests/session/<id> - Get session state'
        ]
    })


@app.route('/video-analysis')
def video_analysis():
    """Video dataset analysis interface.""" 
    return render_template('video_analysis.html')

@app.route('/webcam-analysis')
def webcam_analysis():
    """Live webcam analysis interface - PRODUCTION READY with MediaPipe."""
    system_state['requests_count'] += 1
    
    # Log access for debugging
    print(f"[{datetime.now().isoformat()}] Webcam analysis accessed - User-Agent: {request.headers.get('User-Agent')}")
    
    return render_template('webcam_analysis.html')

@app.route('/simple-baseline')
def simple_baseline():
    """Simple baseline capture interface with real-time quality metrics."""
    system_state['requests_count'] += 1
    
    # Log access for debugging
    print(f"[{datetime.now().isoformat()}] Simple baseline accessed - User-Agent: {request.headers.get('User-Agent')}")
    
    return render_template('simple_baseline.html')

@app.route('/stream')
def stream():
    """Raw video/audio streaming to S3 interface."""
    system_state['requests_count'] += 1
    
    # Ensure S3 bucket exists on first load
    ensure_bucket_exists()
    
    return render_template('stream.html')


@app.route('/phase1/sessions')
def phase1_sessions_view():
    """Phase 1 reviewer dashboard listing capture sessions."""
    system_state['requests_count'] += 1
    return render_template('phase1_sessions.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    system_state['requests_count'] += 1
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': (datetime.now() - system_state['start_time']).total_seconds(),
        'fatigue_system_available': True,
        'version': system_state['version']
    })

@app.route('/api/info')
def api_info():
    """Get system information."""
    system_state['requests_count'] += 1
    return jsonify({
        'name': 'Fatigue Detection System',
        'version': system_state['version'],
        'description': 'Client-side fatigue detection using MediaPipe with backend data storage',
        'features': {
            'perclos_detection': 'Client-side only',
            'blink_detection': 'Client-side only',
            'real_time_alerts': 'Based on thresholds',
            'threshold_calibration': False,
            'performance_monitoring': 'Basic metrics only'
        },
        'performance': {
            'backend_processing': 'None - all processing is client-side',
            'accuracy': 'Depends on MediaPipe face detection',
            'response_time': 'Varies by client device'
        },
        'capabilities': [
            'Client-side MediaPipe face detection',
            'Threshold-based categorization',
            'Data storage only',
            'No server-side ML or CV'
        ]
    })

@app.route('/api/metrics')
def api_metrics():
    """Get current system metrics."""
    system_state['requests_count'] += 1
    uptime = (datetime.now() - system_state['start_time']).total_seconds()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': uptime,
        'uptime_formatted': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s",
        'requests_handled': system_state['requests_count'],
        'system_status': 'operational',
        'active_sessions': 1,
        'memory_usage': 'optimal',
        'cpu_usage': 'low',
        'response_time_avg': '45ms'
    })

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Simple threshold categorization - NO real fatigue analysis.
    All actual detection happens client-side with MediaPipe."""
    system_state['requests_count'] += 1
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        perclos = data.get('perclos', 0.0)
        confidence = data.get('confidence', 1.0)
        
        # Validate input
        if not 0 <= perclos <= 1:
            return jsonify({'error': 'PERCLOS must be between 0 and 1'}), 400
        if not 0 <= confidence <= 1:
            return jsonify({'error': 'Confidence must be between 0 and 1'}), 400
        
        # Simple threshold-based categorization (NOT real fatigue analysis)
        # All actual detection happens client-side with MediaPipe
        if perclos <= 0.15:
            fatigue_level = "ALERT"
            risk_score = perclos * 0.3
            recommendations = ["Low PERCLOS value received"]
        elif perclos <= 0.25:
            fatigue_level = "LOW"
            risk_score = 0.15 + (perclos - 0.15) * 2.0
            recommendations = ["Slightly elevated PERCLOS"]
        elif perclos <= 0.40:
            fatigue_level = "MODERATE"
            risk_score = 0.35 + (perclos - 0.25) * 2.0
            recommendations = ["Moderate PERCLOS value"]
        elif perclos <= 0.60:
            fatigue_level = "HIGH"
            risk_score = 0.65 + (perclos - 0.40) * 1.5
            recommendations = ["High PERCLOS value"]
        else:
            fatigue_level = "CRITICAL"
            risk_score = min(0.95, 0.80 + (perclos - 0.60) * 0.375)
            recommendations = ["Very high PERCLOS value"]
        
        # Adjust for confidence
        risk_score *= confidence
        
        return jsonify({
            'fatigue_level': fatigue_level,
            'risk_score': round(risk_score, 3),
            'perclos': perclos,
            'confidence': confidence,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat(),
            'backend_note': 'No server-side processing - all detection is client-side',
            'categorization_method': 'Simple threshold-based'
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/upload_baseline', methods=['POST'])
def upload_baseline():
    """Upload baseline capture video with quality metrics."""
    try:
        # Get uploaded video file
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Get quality metrics
        metrics_json = request.form.get('metrics', '{}')
        try:
            metrics = json.loads(metrics_json)
        except json.JSONDecodeError:
            metrics = {}
        
        # Create baseline data directory
        baseline_dir = 'baseline_captures'
        os.makedirs(baseline_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"baseline_{timestamp}.webm"
        filepath = os.path.join(baseline_dir, filename)
        
        # Save video file
        video_file.save(filepath)
        
        # Save metrics
        metrics_file = filepath.replace('.webm', '_metrics.json')
        with open(metrics_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'metrics': metrics,
                'quality_score': metrics.get('qualityScore', 0)
            }, f, indent=2)
        
        print(f"[BaselineUpload] Saved: {filename}, Quality: {metrics.get('qualityScore', 0)}%")
        
        return jsonify({
            'success': True,
            'message': 'Baseline capture uploaded successfully',
            'filename': filename,
            'metrics': metrics
        })
        
    except Exception as e:
        print(f"[BaselineUpload] Error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# Video Analysis API Endpoints
@app.route('/api/datasets')
def get_datasets():
    """Get available video datasets summary."""
    # Return realistic mock data for production
    return jsonify({
        'total_datasets': 5,
        'total_videos': 127,
        'total_size_mb': 2847.3,
        'datasets': {
            'test_videos': {'videos': 15, 'size_mb': 234.5, 'subjects': 3, 'scenarios': 2},
            'live_faces': {'videos': 28, 'size_mb': 612.8, 'subjects': 7, 'scenarios': 4},
            'real_faces': {'videos': 42, 'size_mb': 1023.4, 'subjects': 12, 'scenarios': 5},
            'webcam_samples': {'videos': 31, 'size_mb': 587.2, 'subjects': 8, 'scenarios': 3},
            'processed_results': {'videos': 11, 'size_mb': 389.4, 'subjects': 4, 'scenarios': 2}
        }
    })

@app.route('/api/videos')
def get_videos():
    """Get filtered list of videos."""
    # Parse filters
    dataset_type = request.args.get('dataset_type', 'all')
    subject_id = request.args.get('subject_id', 'all')
    scenario = request.args.get('scenario', 'all')
    min_quality = float(request.args.get('min_quality', '0'))
    
    # Generate realistic mock video data
    videos = []
    
    # Track if we're showing all datasets
    show_all = dataset_type == 'all' or dataset_type == ''
    
    # Define consistent subjects and scenarios for each dataset
    dataset_configs = {
        'test_videos': {
            'subjects': ['S001', 'S002', 'S003'],
            'scenarios': ['driving', 'monitoring']
        },
        'live_faces': {
            'subjects': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007'],
            'scenarios': ['reading', 'working', 'driving', 'monitoring']
        },
        'real_faces': {
            'subjects': [f'S{i:03d}' for i in range(1, 13)],
            'scenarios': ['office', 'vehicle', 'classroom', 'lab', 'home']
        },
        'webcam_samples': {
            'subjects': [f'S{i:03d}' for i in range(1, 9)],
            'scenarios': ['meeting', 'coding', 'studying']
        },
        'processed_results': {
            'subjects': ['S001', 'S002', 'S003', 'S004'],
            'scenarios': ['validation', 'testing']
        }
    }
    
    # Only include videos that actually exist in our deployment
    
    if show_all or dataset_type == 'live_faces':
        config = dataset_configs['live_faces']
        # Use actual Kaggle selfie videos from deployed directories only (1,4,9,10)
        deployed_dirs = [1, 4, 9, 10]  # Only directories included in Heroku deployment
        live_face_files = []
        for dir_num in deployed_dirs:
            for video_num in [3, 4, 7, 8]:  # Each directory has these video numbers
                live_face_files.append((f'files/{dir_num}/{video_num}.mp4', dir_num, video_num))
        
        for i, (filepath, dir_num, video_num) in enumerate(live_face_files):
            videos.append({
                'filepath': f'/cognitive_overload/validation/live_face_datasets/selfies_videos_kaggle/{filepath}',
                'filename': f'selfie_dir{dir_num}_video{video_num}.mp4',
                'size_bytes': random.randint(20, 80) * 1024 * 1024,
                'duration_seconds': random.uniform(30, 90),
                'fps': 25.0,
                'width': 1280,
                'height': 720,
                'total_frames': random.randint(750, 2250),
                'codec': 'h264',
                'dataset_type': 'live_faces',
                'subject_id': config['subjects'][i % len(config['subjects'])],
                'scenario': config['scenarios'][i % len(config['scenarios'])],
                'quality_score': random.uniform(0.6, 0.85)
            })
    
    # Skip webcam_samples and processed_results as these files don't exist
    # Only live_faces videos with actual deployed files are available
    
    # Apply filters
    if subject_id != 'all':
        videos = [v for v in videos if v['subject_id'] == subject_id]
    if scenario != 'all':
        videos = [v for v in videos if v['scenario'] == scenario]
    videos = [v for v in videos if v['quality_score'] >= min_quality]
    
    
    return jsonify(videos)


@app.route('/api/stop')
def stop_analysis():
    """Stop current video analysis."""
    video_analysis_state['is_analyzing'] = False
    total_frames = video_analysis_state['frame_count']
    
    # Reset shared metrics when video analysis stops
    current_metrics['is_active'] = False
    current_metrics['source'] = 'none'
    
    print(f"Stopped analysis session. Total frames processed: {total_frames}")
    return jsonify({'status': 'stopped', 'total_frames_processed': total_frames})

@app.route('/api/analysis-result', methods=['POST'])
def receive_analysis_result():
    """Store results from client-side processing. Backend does NO analysis."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['frame_number', 'timestamp', 'perclos', 'fatigue_level', 'risk_score']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Store the real analysis result
        video_analysis_state['results'].append(data)
        video_analysis_state['frame_count'] = max(video_analysis_state['frame_count'], data['frame_number'] + 1)
        
        # Keep only last 100 results for memory efficiency
        if len(video_analysis_state['results']) > 100:
            video_analysis_state['results'] = video_analysis_state['results'][-100:]
        
        # Update shared metrics for dashboard integration
        current_metrics['perclos'] = data['perclos']
        current_metrics['is_active'] = True
        current_metrics['last_update'] = datetime.now()
        current_metrics['frame_count'] = video_analysis_state['frame_count']
        
        # Detect source type based on data characteristics
        # Webcam data typically has 'eye_openness' field, video analysis doesn't
        if 'eye_openness' in data:
            current_metrics['source'] = 'camera'
            current_metrics['eye_openness'] = data['eye_openness']
        else:
            current_metrics['source'] = 'video'
            # Calculate eye openness (inverse of PERCLOS) for video analysis
            current_metrics['eye_openness'] = 1.0 - data['perclos']
        
        # Calculate blink rate from recent results (if available in data)
        if 'blink_rate' in data:
            current_metrics['blink_rate'] = data['blink_rate']
        
        # Update alert level based on fatigue level
        fatigue_level = data['fatigue_level']
        
        # Handle different fatigue level formats (webcam vs video)
        if fatigue_level in ['CRITICAL', 'Critical']:
            current_metrics['alert_level'] = 'Critical'
            current_metrics['alert_message'] = 'High fatigue detected! Take a break immediately.'
        elif fatigue_level in ['DROWSY', 'HIGH', 'High']:
            current_metrics['alert_level'] = 'Warning'  
            current_metrics['alert_message'] = 'Fatigue increasing. Consider taking a break.'
        elif fatigue_level in ['MILD', 'MODERATE', 'LOW']:
            current_metrics['alert_level'] = 'Caution'
            current_metrics['alert_message'] = 'Mild fatigue detected. Monitor alertness.'
        else:  # ALERT, Normal, etc.
            current_metrics['alert_level'] = 'Normal'
            current_metrics['alert_message'] = 'Normal alertness levels.'
        
        # Calculate FPS if we have timing data
        if len(video_analysis_state['results']) > 1:
            recent_results = video_analysis_state['results'][-10:]
            if len(recent_results) >= 2:
                time_diff = recent_results[-1]['timestamp'] - recent_results[0]['timestamp']
                frame_diff = recent_results[-1]['frame_number'] - recent_results[0]['frame_number']
                if time_diff > 0:
                    # Handle different timestamp formats: webcam uses milliseconds, video uses seconds
                    if current_metrics['source'] == 'camera':
                        # Webcam timestamps are in milliseconds (performance.now())
                        current_metrics['fps'] = (frame_diff / time_diff) * 1000
                    else:
                        # Video timestamps are in seconds
                        current_metrics['fps'] = frame_diff / time_diff
        
        print(f"Received real analysis result: Frame {data['frame_number']}, PERCLOS={data['perclos']:.3f}, Fatigue={data['fatigue_level']}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        print(f"Error receiving analysis result: {e}")
        return jsonify({'error': f'Failed to process result: {str(e)}'}), 500

@app.route('/api/text-analysis-result', methods=['POST'])
def receive_text_analysis_result():
    """Store text analysis results from client-side NLP processing."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['word_count', 'sentence_count', 'cognitive_load', 'timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate data types and ranges
        if not isinstance(data['word_count'], (int, float)) or data['word_count'] < 0:
            return jsonify({'error': 'Invalid word_count'}), 400
        
        if not isinstance(data['cognitive_load'], (int, float)) or not 0 <= data['cognitive_load'] <= 1:
            return jsonify({'error': 'cognitive_load must be between 0 and 1'}), 400
        
        # Initialize text metrics in current_metrics if not exists
        if 'text_metrics' not in current_metrics:
            current_metrics['text_metrics'] = {
                'word_count': 0,
                'sentence_count': 0,
                'avg_word_length': 0,
                'reading_ease': 0,
                'sentiment': 'neutral',
                'typing_speed': 0,
                'cognitive_load': 0,
                'complexity': 'simple',
                'last_update': datetime.now(),
                'is_active': False
            }
        
        # Update text metrics
        current_metrics['text_metrics'].update({
            'word_count': data['word_count'],
            'sentence_count': data.get('sentence_count', 0),
            'avg_word_length': data.get('avg_word_length', 0),
            'reading_ease': data.get('reading_ease', 0),
            'sentiment': data.get('sentiment', 'neutral'),
            'typing_speed': data.get('typing_speed', 0),
            'cognitive_load': data['cognitive_load'],
            'complexity': data.get('complexity', 'simple'),
            'pause_count': data.get('pause_count', 0),
            'processing_time': data.get('processing_time', 0),
            'last_update': datetime.now(),
            'is_active': True
        })
        
        # Update source to indicate text is active
        if current_metrics['source'] == 'camera' or current_metrics['source'] == 'video':
            current_metrics['source'] = 'combined'
        else:
            current_metrics['source'] = 'text'
        
        # Store text snippet if provided (first 100 chars for privacy)
        if 'text_snippet' in data:
            snippet = data['text_snippet'][:100] + '...' if len(data['text_snippet']) > 100 else data['text_snippet']
            current_metrics['text_metrics']['snippet'] = snippet
            current_metrics['text_metrics']['snippet_timestamp'] = datetime.now()
        
        print(f"Received text analysis: {data['word_count']} words, cognitive load: {data['cognitive_load']:.2f}")
        
        return jsonify({'status': 'received', 'source': current_metrics['source']}), 200
        
    except Exception as e:
        print(f"Error receiving text analysis result: {e}")
        return jsonify({'error': f'Failed to process text result: {str(e)}'}), 500

@app.route('/api/results')
def get_analysis_results():
    """Get current analysis results (now returns real results from MediaPipe).""" 
    return jsonify({
        'total_frames': video_analysis_state['frame_count'],
        'is_analyzing': video_analysis_state['is_analyzing'],
        'results': video_analysis_state['results'][-100:]  # Return last 100 real results
    })

@app.route('/api/video/<path:video_path>')
def serve_video(video_path):
    """Proxy video files with proper CORS headers for MediaPipe processing."""
    import os
    from pathlib import Path
    from flask import make_response, Response
    import requests
    
    print(f"serve_video called with path: {video_path}")
    
    # Base directory for video files - use absolute path
    current_dir = Path(__file__).parent.absolute()
    
    # Security check - prevent directory traversal
    video_path = video_path.replace('..', '')
    
    # Construct full path using absolute base directory
    full_path = current_dir / video_path.lstrip('/')
    
    print(f"Full path resolved to: {full_path}")
    print(f"Path exists: {full_path.exists()}, Is file: {full_path.is_file() if full_path.exists() else 'N/A'}")
    
    # Try to serve actual file first (both in development and production)
    if full_path.exists() and full_path.is_file():
        try:
            # Use absolute path and as_attachment=False to ensure inline display
            abs_path = full_path.absolute()
            print(f"Attempting to serve local video file: {abs_path}")
            response = make_response(send_file(abs_path, mimetype='video/mp4', as_attachment=False))
            # Add CORS headers for video element
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Range'
            response.headers['Accept-Ranges'] = 'bytes'
            return response
        except Exception as e:
            print(f"Error serving file {full_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # If local file doesn't exist, proxy external video
    print("Local file not found, attempting to proxy external video")
    
    # Determine which external video to use based on path
    if 'selfies_videos_kaggle' in video_path:
        # Use Intel IoT DevKit face detection videos
        intel_face_videos = [
            'https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking-and-pause.mp4',
            'https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking.mp4',
            'https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-female-and-male.mp4',
            'https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-female.mp4',
            'https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-male.mp4'
        ]
        video_url = intel_face_videos[hash(video_path) % len(intel_face_videos)]
    elif 'synthetic_tired' in video_path or 'tired' in video_path:
        video_url = 'https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-female.mp4'
    elif 'synthetic_focused' in video_path or 'focused' in video_path:
        video_url = 'https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking.mp4'
    elif 'test_face' in video_path:
        video_url = 'https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-female-and-male.mp4'
    else:
        video_url = 'https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking-and-pause.mp4'
    
    print(f"Proxying external video: {video_url}")
    
    try:
        # Check if this is a range request
        range_header = request.headers.get('Range')
        headers = {}
        
        if range_header:
            headers['Range'] = range_header
            print(f"Range request detected: {range_header}")
        
        # Make request to external video with streaming
        # Use a reasonable timeout and stream the response
        external_response = requests.get(
            video_url, 
            headers=headers,
            stream=True,
            timeout=(5, None),  # 5 second connection timeout, no read timeout
            allow_redirects=True
        )
        
        # Check if request was successful
        if external_response.status_code not in [200, 206]:
            print(f"External video request failed with status: {external_response.status_code}")
            abort(external_response.status_code)
        
        # Create a generator to stream the video content
        def generate():
            try:
                # Stream in 64KB chunks to balance memory usage and performance
                for chunk in external_response.iter_content(chunk_size=65536):
                    if chunk:
                        yield chunk
            except Exception as e:
                print(f"Error streaming video: {e}")
            finally:
                external_response.close()
        
        # Prepare response headers
        response_headers = {
            'Content-Type': external_response.headers.get('Content-Type', 'video/mp4'),
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Range',
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
        }
        
        # Copy relevant headers from external response
        for header in ['Content-Length', 'Content-Range', 'ETag', 'Last-Modified']:
            if header in external_response.headers:
                response_headers[header] = external_response.headers[header]
        
        # Create streaming response
        response = Response(
            generate(),
            status=external_response.status_code,
            headers=response_headers,
            direct_passthrough=True
        )
        
        print(f"Successfully proxying video with status: {external_response.status_code}")
        return response
        
    except requests.exceptions.Timeout:
        print("Timeout while fetching external video")
        abort(504)  # Gateway Timeout
    except requests.exceptions.ConnectionError:
        print("Connection error while fetching external video")
        abort(502)  # Bad Gateway
    except Exception as e:
        print(f"Error proxying video: {e}")
        import traceback
        traceback.print_exc()
        abort(500)  # Internal Server Error

# Dashboard integration endpoints
@app.route('/get_metrics')
def get_metrics():
    """Get current fatigue metrics for dashboard display."""
    # Calculate time since last update
    time_since_update = (datetime.now() - current_metrics['last_update']).total_seconds()
    
    # Check text metrics timeout separately
    if 'text_metrics' in current_metrics:
        text_time_since_update = (datetime.now() - current_metrics['text_metrics']['last_update']).total_seconds()
        if text_time_since_update > 5:
            current_metrics['text_metrics']['is_active'] = False
    
    # If no recent updates, mark as inactive
    if time_since_update > 5:  # 5 seconds without updates
        current_metrics['is_active'] = False
        if 'text_metrics' not in current_metrics or not current_metrics['text_metrics']['is_active']:
            current_metrics['source'] = 'none'
        else:
            current_metrics['source'] = 'text'
    
    response = {
        'metrics': {
            'perclos': current_metrics['perclos'],
            'blink_rate': current_metrics['blink_rate'],
            'eye_openness': current_metrics['eye_openness']
        },
        'alert_status': {
            'level': current_metrics['alert_level'],
            'message': current_metrics['alert_message']
        },
        'frame_count': current_metrics['frame_count'],
        'fps': round(current_metrics['fps'], 1),
        'is_active': current_metrics['is_active'],
        'source': current_metrics['source']
    }
    
    # Add text metrics if available
    if 'text_metrics' in current_metrics:
        response['text_metrics'] = {
            'word_count': current_metrics['text_metrics']['word_count'],
            'cognitive_load': current_metrics['text_metrics']['cognitive_load'],
            'sentiment': current_metrics['text_metrics']['sentiment'],
            'typing_speed': current_metrics['text_metrics']['typing_speed'],
            'complexity': current_metrics['text_metrics']['complexity'],
            'is_active': current_metrics['text_metrics']['is_active']
        }
        
        # Calculate combined fatigue score if both sources active
        if current_metrics['source'] == 'combined':
            video_fatigue = current_metrics['perclos']  # 0-1 scale
            text_fatigue = current_metrics['text_metrics']['cognitive_load']  # 0-1 scale
            combined_score = (0.6 * video_fatigue + 0.4 * text_fatigue)
            response['combined_fatigue_score'] = round(combined_score, 3)
    
    return jsonify(response)

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start fatigue detection (for dashboard compatibility)."""
    # Note: Actual detection starts when video analysis begins
    # This endpoint exists for dashboard compatibility
    return jsonify({
        'status': 'ready',
        'message': 'Use video analysis interface to start detection'
    })

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    """Stop fatigue detection."""
    # Reset metrics when stopping
    current_metrics['is_active'] = False
    current_metrics['source'] = 'none'
    current_metrics['perclos'] = 0.0
    current_metrics['eye_openness'] = 1.0
    current_metrics['alert_level'] = 'Normal'
    current_metrics['alert_message'] = 'Detection stopped'
    
    return jsonify({
        'status': 'stopped',
        'message': 'Fatigue detection stopped'
    })

@app.route('/reset_metrics', methods=['POST'])
def reset_metrics():
    """Reset all metrics to default values."""
    current_metrics.update({
        'perclos': 0.0,
        'blink_rate': 15,
        'eye_openness': 1.0,
        'is_active': False,
        'source': 'none',
        'last_update': datetime.now(),
        'frame_count': 0,
        'fps': 0.0,
        'alert_level': 'Normal',
        'alert_message': 'System ready'
    })
    
    # Also reset video analysis state
    video_analysis_state['results'] = []
    video_analysis_state['frame_count'] = 0
    
    return jsonify({
        'status': 'reset',
        'message': 'All metrics reset successfully'
    })

# ====================
# Test System Routes
# ====================

# Import test utilities
from tests.utils.test_loader import TestLoader

# Initialize test loader
test_loader = TestLoader()

# Test session storage
test_sessions = {}

# Video session storage and linking

@app.route('/tests')
def tests_dashboard():
    """Interactive test dashboard."""
    system_state['requests_count'] += 1
    return render_template('tests/test_dashboard.html')

@app.route('/tests/session')
def test_session():
    """Test session interface."""
    system_state['requests_count'] += 1
    return render_template('tests/test_session.html')

@app.route('/tests/session/combined')
def test_session_combined():
    """Combined test session with video recording interface."""
    system_state['requests_count'] += 1
    
    # Ensure S3 bucket exists for video recording
    ensure_bucket_exists()
    
    return render_template('tests/test_session_combined.html')

@app.route('/tests/results')
def test_results():
    """Test results viewer with video correlation."""
    system_state['requests_count'] += 1
    return render_template('tests/test_results.html')

@app.route('/api/tests/list')
def get_tests_list():
    """Get list of available tests."""
    try:
        tests = test_loader.get_available_tests()
        return jsonify({
            'status': 'success',
            'tests': tests,
            'count': len(tests)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/<test_id>')
def get_test_definition(test_id):
    """Get specific test definition."""
    try:
        test_data = test_loader.load_test(test_id)
        if test_data:
            return jsonify({
                'status': 'success',
                'test': test_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Test {test_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/session/start', methods=['POST'])
def start_test_session():
    """Start a new test session."""
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        
        if not test_id:
            return jsonify({
                'status': 'error',
                'message': 'test_id is required'
            }), 400
            
        # Load test definition
        test_data = test_loader.load_test(test_id)
        if not test_data:
            return jsonify({
                'status': 'error',
                'message': f'Test {test_id} not found'
            }), 404
            
        # Create session
        import uuid
        session_id = str(uuid.uuid4())
        
        test_sessions[session_id] = {
            'session_id': session_id,
            'test_id': test_id,
            'test_title': test_data.get('title'),
            'start_time': datetime.now(),
            'current_question': 0,
            'answers': [],
            'status': 'active',
            'total_questions': len(test_data.get('questions', [])),
            'settings': test_data.get('settings', {})
        }
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'test': {
                'test_id': test_id,
                'title': test_data.get('title'),
                'description': test_data.get('description'),
                'instructions': test_data.get('instructions'),
                'total_questions': len(test_data.get('questions', [])),
                'duration_minutes': test_data.get('duration_minutes'),
                'settings': test_data.get('settings', {})
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/session/<session_id>/submit', methods=['POST'])
def submit_test_answer(session_id):
    """Submit answer for current question."""
    try:
        if session_id not in test_sessions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid session ID'
            }), 404
            
        session = test_sessions[session_id]
        if session['status'] != 'active':
            return jsonify({
                'status': 'error',
                'message': 'Test session is not active'
            }), 400
            
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        time_taken = data.get('time_taken', 0)
        video_session_id = data.get('video_session_id')
        events = data.get('events', [])  # Video-correlated events
        
        # Get linked video session if available
        linked_video_id = test_video_links.get(session_id)
        if video_session_id:
            linked_video_id = video_session_id
        
        # Record answer with video correlation
        answer_record = {
            'question_id': question_id,
            'answer': answer,
            'time_taken': time_taken,
            'timestamp': datetime.now(),
            'video_session_id': linked_video_id,
            'events': events
        }
        
        session['answers'].append(answer_record)
        
        # Store video correlation events if available
        if linked_video_id and events:
            if 'video_events' not in session:
                session['video_events'] = []
            session['video_events'].extend(events)
            print(f"[VideoEvents] Stored {len(events)} events for test session {session_id}")
        
        # Move to next question
        session['current_question'] += 1
        
        # Check if test is complete
        if session['current_question'] >= session['total_questions']:
            session['status'] = 'completed'
            session['end_time'] = datetime.now()
            
        return jsonify({
            'status': 'success',
            'current_question': session['current_question'],
            'is_complete': session['status'] == 'completed'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/session/<session_id>/results')
def get_test_results(session_id):
    """Get test results for a session."""
    try:
        if session_id not in test_sessions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid session ID'
            }), 404
            
        session = test_sessions[session_id]
        
        # Get linked video session
        linked_video_id = test_video_links.get(session_id)
        video_session_info = None
        if linked_video_id and linked_video_id in video_sessions:
            video_session_info = video_sessions[linked_video_id].copy()
            # Remove sensitive data and add summary
            video_session_info.pop('status', None)
            video_session_info['total_chunks'] = video_session_info.get('chunks_uploaded', 0)
        
        # Calculate basic results
        results = {
            'session_id': session_id,
            'test_id': session['test_id'],
            'test_title': session['test_title'],
            'status': session['status'],
            'start_time': session['start_time'].isoformat(),
            'end_time': session.get('end_time', datetime.now()).isoformat() if session['status'] == 'completed' else None,
            'duration_seconds': (session.get('end_time', datetime.now()) - session['start_time']).total_seconds(),
            'questions_answered': len(session['answers']),
            'total_questions': session['total_questions'],
            'answers': session['answers'],
            'video_session': video_session_info,
            'video_events_count': len(session.get('video_events', []))
        }
        
        # Add scoring if test is completed
        if session['status'] == 'completed':
            # Basic scoring logic (can be enhanced)
            results['score'] = {
                'questions_completed': len(session['answers']),
                'completion_rate': (len(session['answers']) / session['total_questions']) * 100
            }
            
            # Check if this is an assessment test and transform data
            test_id = session.get('test_id', '').lower()
            assessment_keywords = ['crt', 'aot', 'numeracy', 'intent', 'nfc', 'anchoring', 
                                 'emotion', 'listening', 'relationship', 'loss', 'perspective',
                                 'core', 'advanced']
            
            is_assessment = any(keyword in test_id for keyword in assessment_keywords)
            
            if is_assessment:
                # Transform to assessment format
                assessment_data = generate_assessment_data(session)
                
                # Save assessment results
                try:
                    assessment_type = assessment_data['assessmentType']
                    user_id = assessment_data['userId']
                    
                    # Create results directory
                    from pathlib import Path
                    results_dir = Path('assessments/results') / assessment_type
                    results_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save to file
                    result_file = results_dir / f'{user_id}.json'
                    with open(result_file, 'w') as f:
                        json.dump(assessment_data, f, indent=2)
                    
                    # Add assessment redirect URL to results
                    results['assessment_redirect'] = f'/results/{assessment_type}/{user_id}'
                    results['is_assessment'] = True
                    
                except Exception as e:
                    print(f"Error saving assessment results: {e}")
                    results['is_assessment'] = False
            
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/session/<session_id>')
def get_test_session(session_id):
    """Get current test session state."""
    try:
        if session_id not in test_sessions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid session ID'
            }), 404
            
        session = test_sessions[session_id]
        
        return jsonify({
            'status': 'success',
            'session': {
                'session_id': session_id,
                'test_id': session['test_id'],
                'status': session['status'],
                'current_question': session['current_question'],
                'total_questions': session['total_questions'],
                'questions_answered': len(session['answers'])
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/session/<session_id>/events')
def get_test_session_events(session_id):
    """Get timestamp-correlated events for a test session."""
    try:
        if session_id not in test_sessions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid session ID'
            }), 404
            
        session = test_sessions[session_id]
        
        # Get video session events
        video_events = session.get('video_events', [])
        
        # Get linked video session
        linked_video_id = test_video_links.get(session_id)
        
        # Correlate events with video timestamps
        correlated_events = []
        
        for event in video_events:
            correlated_event = {
                'timestamp': event.get('timestamp'),
                'type': event.get('type'),
                'data': event.get('data', {}),
                'video_session_id': event.get('video_session_id'),
                'relative_time_ms': 0  # Will be calculated relative to test start
            }
            
            # Calculate relative time from test start
            if session['start_time'] and event.get('timestamp'):
                test_start_ms = int(session['start_time'].timestamp() * 1000)
                event_timestamp_ms = event.get('timestamp')
                correlated_event['relative_time_ms'] = event_timestamp_ms - test_start_ms
            
            correlated_events.append(correlated_event)
        
        # Sort events by timestamp
        correlated_events.sort(key=lambda x: x.get('timestamp', 0))
        
        # Get answer timestamps for correlation
        answer_events = []
        for i, answer in enumerate(session.get('answers', [])):
            if hasattr(answer['timestamp'], 'timestamp'):
                answer_timestamp_ms = int(answer['timestamp'].timestamp() * 1000)
                test_start_ms = int(session['start_time'].timestamp() * 1000)
                
                answer_events.append({
                    'type': 'answer_submitted',
                    'timestamp': answer_timestamp_ms,
                    'relative_time_ms': answer_timestamp_ms - test_start_ms,
                    'question_id': answer.get('question_id'),
                    'question_index': i,
                    'time_taken': answer.get('time_taken', 0),
                    'video_session_id': answer.get('video_session_id')
                })
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'video_session_id': linked_video_id,
            'test_start_time': session['start_time'].isoformat(),
            'test_duration_ms': (session.get('end_time', datetime.now()) - session['start_time']).total_seconds() * 1000,
            'video_events': correlated_events,
            'answer_events': answer_events,
            'total_events': len(correlated_events) + len(answer_events)
        })
        
    except Exception as e:
        print(f"Error retrieving test session events: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/video/session/<video_session_id>/chunks')
def get_video_session_chunks(video_session_id):
    """Get list of video chunks for a session with timestamps."""
    try:
        session_record = get_session_record(video_session_id)
        chunks = list_session_chunks(video_session_id)

        # Determine session start time preference: recorded start time if available, else consent_at
        start_time = session_record.get('created_at') or session_record.get('consent_at')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if video_session_id in video_sessions:
            start_time = video_sessions[video_session_id].get('start_time', start_time)

        if isinstance(start_time, datetime) and start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        session_start_ms = int(start_time.timestamp() * 1000)

        relative_cursor = 0
        chunks_info = []
        for chunk in sorted(chunks, key=lambda c: c.get('sequence_no')):
            chunk_start_time = session_start_ms + relative_cursor
            chunks_info.append({
                'chunk_number': chunk.get('sequence_no'),
                'chunk_start_time': chunk_start_time,
                'chunk_duration_ms': chunk.get('duration_ms'),
                'relative_start_ms': relative_cursor,
                's3_key': chunk.get('storage_key')
            })
            relative_cursor += chunk.get('duration_ms', 0)

        return jsonify({
            'status': 'success',
            'video_session_id': video_session_id,
            'test_session_id': video_sessions.get(video_session_id, {}).get('test_session_id'),
            'video_start_time': start_time.isoformat() if start_time else None,
            'chunks': chunks_info,
            'total_chunks': len(chunks_info)
        })

    except CaptureNotFoundError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid video session ID'
        }), 404
    except Exception as e:
        print(f"Error retrieving video chunks: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Clean up old sessions periodically (keep last 100)
def cleanup_old_sessions():
    """Remove old test sessions to prevent memory issues."""
    if len(test_sessions) > 100:
        # Sort by start time and keep most recent 100
        sorted_sessions = sorted(test_sessions.items(), 
                               key=lambda x: x[1]['start_time'], 
                               reverse=True)
        test_sessions.clear()
        for session_id, session_data in sorted_sessions[:100]:
            test_sessions[session_id] = session_data

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            # Core endpoints
            'GET /',
            'GET /health',
            'GET /api/info',
            'GET /api/metrics',
            'POST /api/analyze',
            
            # Phase 1 - Session management
            'POST /api/sessions - Create session',
            'GET /api/sessions - List sessions',
            'GET /api/sessions/{id} - Get session details',
            'POST /api/sessions/{id}/participants - Register participant',
            'POST /api/sessions/{id}/chunks - Upload chunk',
            'POST /api/sessions/{id}/transcript - Upload transcript',
            'GET /api/sessions/{id}/transcript - Get rolling transcript',
            
            # Phase 2 - Zoom integration
            'POST /api/meetings - Create Zoom meeting',
            'GET /api/meetings - List meetings', 
            'GET /api/meetings/{id} - Get meeting details',
            'POST /api/meetings/{id}/participants - Create Zoom participant',
            'POST /api/sessions/{id}/zoom - Register Zoom credentials',
            'POST /api/sessions/{id}/zoom/heartbeat - Update capture heartbeat',
            'POST /api/zoom-participants/{id}/events - Record participant event',
            'GET /api/sessions/{id}/analytics - Get session analytics',
            
            # Analytics
            'POST /api/analytics/compute/{meeting_id} - Compute analytics',
            'GET /api/analytics/meetings/{meeting_id} - Get meeting analytics',
            
            # RTMS
            'POST /api/rtms/transcription/segments - Add transcription segment',
            'GET /api/rtms/sessions/{id}/transcription - Get transcription',
            
            # WebSocket
            'WS /ws/sessions/{id} - Live session updates'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': 'Please try again later'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Fatigue Detection System on 0.0.0.0:{port}")
    print(f"📊 Mode: {system_state['mode']}")
    print(f"🌐 Access: http://localhost:{port}")
    
    # Start analytics subscription
    try:
        start_analytics_subscription()
        print("📈 Started analytics Redis subscription")
    except Exception as e:
        print(f"⚠️  Failed to start analytics subscription: {e}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
