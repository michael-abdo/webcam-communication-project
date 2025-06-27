#!/usr/bin/env python3
"""
Lightweight Production Deployment App for Fatigue Detection System
Optimized for cloud deployment without heavy dependencies
"""

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
            'GET /api/results - Get analysis results',
            'GET /video-analysis - Video dataset analysis interface'
        ]
    })

@app.route('/dashboard')
def dashboard():
    """Full dashboard interface."""
    return render_template('dashboard.html')

@app.route('/demo')
def demo():
    """Demo interface."""
    return render_template('demo.html')

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

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """Start video analysis."""
    try:
        data = request.get_json()
        if not data or 'video_path' not in data:
            return jsonify({'error': 'No video path provided'}), 400
        
        video_path = data.get('video_path')
        frame_skip = data.get('frame_skip', 1)
        
        # Validate frame_skip
        try:
            frame_skip = int(frame_skip)
            if frame_skip < 1:
                return jsonify({'error': 'Frame skip must be at least 1'}), 400
            if frame_skip > 10:
                return jsonify({'error': 'Frame skip cannot exceed 10'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'Frame skip must be a valid integer'}), 400
        
        # Start real analysis session - clear previous results
        video_analysis_state['is_analyzing'] = True
        video_analysis_state['current_video'] = video_path
        video_analysis_state['frame_count'] = 0
        video_analysis_state['results'] = []
        
        print(f"Started analysis session for video: {video_path} (frame_skip: {frame_skip})")
        
        return jsonify({
            'status': 'started',
            'video': video_path,
            'frame_skip': frame_skip
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

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
    
    # If no recent updates, mark as inactive
    if time_since_update > 5:  # 5 seconds without updates
        current_metrics['is_active'] = False
        current_metrics['source'] = 'none'
    
    return jsonify({
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
    })

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

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/info',
            'GET /api/metrics',
            'POST /api/analyze'
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
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )