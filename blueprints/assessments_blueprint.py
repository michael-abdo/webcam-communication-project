"""
Flask Blueprint for Assessment functionality
"""
from flask import Blueprint, render_template, jsonify, request, send_from_directory, send_file
from pathlib import Path
import json
import os
from datetime import datetime
from utils.scoring import calculate_assessment_scores

# Create the blueprint
assessment_bp = Blueprint('assessments', __name__, url_prefix='')

# Paths for assessment files
ASSESSMENT_DIR = Path(__file__).parent.parent / 'assessments'
STATIC_DIR = ASSESSMENT_DIR / 'static'
RESULTS_DIR = ASSESSMENT_DIR / 'results'
TEMPLATES_DIR = Path(__file__).parent.parent / 'templates' / 'assessments'

# Create results directories if they don't exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / 'core').mkdir(exist_ok=True)
(RESULTS_DIR / 'advanced').mkdir(exist_ok=True)

# Home page route
@assessment_bp.route('/assessment')
@assessment_bp.route('/assessment/')
def home():
    """Home page with assessment options"""
    # Generate the home page HTML
    
    # For now, return a simple HTML response
    # In production, you'd use a proper template
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bias-Resilient Assessment Platform</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .assessment-list {
                list-style: none;
                padding: 0;
            }
            .assessment-item {
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 8px;
                border-left: 4px solid #2196f3;
            }
            .assessment-item h3 {
                margin-top: 0;
                color: #2196f3;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background: #2196f3;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #1976d2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Bias-Resilient Assessment Platform</h1>
            <p>Welcome to the interactive assessment platform. Choose an assessment to begin:</p>
            
            <ul class="assessment-list">
                <li class="assessment-item">
                    <h3>Cognitive Reflection Test (CRT)</h3>
                    <p>Measure your intuitive vs deliberative thinking style with classic reasoning problems.</p>
                    <a href="/assessment/crt" class="btn">Start CRT Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Actively Open-Minded Thinking (AOT)</h3>
                    <p>Assess your intellectual humility and resistance to cognitive biases.</p>
                    <a href="/assessment/aot" class="btn">Start AOT Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Reaction Time & Fatigue Test</h3>
                    <p>Test your reaction speed and detect any cognitive fatigue.</p>
                    <a href="/assessment/reaction" class="btn">Start Reaction Test</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Full Core Assessment (4 minutes)</h3>
                    <p>Complete cognitive assessment including CRT, AOT, numeracy, and intent attribution.</p>
                    <a href="/assessment/core" class="btn">Start Core Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Full Advanced Assessment (6 minutes)</h3>
                    <p>Personality and behavioral assessment including emotion regulation and decision biases.</p>
                    <a href="/assessment/advanced" class="btn">Start Advanced Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Baseline Capture Setup</h3>
                    <p>Calibrate the system to your unique patterns for personalized assessments (25 seconds).</p>
                    <a href="/assessment/baseline" class="btn">Start Baseline Setup</a>
                </li>
            </ul>
        </div>
    </body>
    </html>
    """
    return html_content

# Individual assessment routes
@assessment_bp.route('/assessment/crt')
def crt_assessment():
    """Serve the CRT assessment page"""
    file_path = STATIC_DIR / 'crt_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/aot')
def aot_assessment():
    """Serve the AOT assessment page"""
    file_path = STATIC_DIR / 'aot_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/reaction')
def reaction_assessment():
    """Serve the reaction time assessment page"""
    file_path = STATIC_DIR / 'reaction_time_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/core')
def core_assessment():
    """Serve the full Core assessment page"""
    file_path = STATIC_DIR / 'core_assessment.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/numeracy')
def numeracy_assessment():
    """Serve the numeracy assessment page"""
    file_path = STATIC_DIR / 'numeracy_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/intent')
def intent_assessment():
    """Serve the intent attribution assessment page"""
    file_path = STATIC_DIR / 'intent_attribution_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/nfc')
def nfc_assessment():
    """Serve the need for closure assessment page"""
    file_path = STATIC_DIR / 'need_for_closure_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/anchoring')
def anchoring_assessment():
    """Serve the anchoring test page"""
    file_path = STATIC_DIR / 'anchoring_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/advanced')
def advanced_assessment():
    """Serve the full Advanced assessment page"""
    file_path = STATIC_DIR / 'advanced_assessment.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/emotion-regulation')
def emotion_regulation_assessment():
    """Serve the emotion regulation assessment page"""
    file_path = STATIC_DIR / 'emotion_regulation_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/relationship-style')
def relationship_style_assessment():
    """Serve the relationship style assessment page"""
    file_path = STATIC_DIR / 'relationship_style_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/listening-preferences')
def listening_preferences_assessment():
    """Serve the listening preferences assessment page"""
    file_path = STATIC_DIR / 'listening_preferences_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/loss-aversion')
def loss_aversion_assessment():
    """Serve the loss aversion assessment page"""
    file_path = STATIC_DIR / 'loss_aversion_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/perspective-taking')
def perspective_taking_assessment():
    """Serve the perspective taking assessment page"""
    file_path = STATIC_DIR / 'perspective_taking_simple.html'
    return send_file(file_path)

@assessment_bp.route('/assessment/baseline')
def baseline_capture_assessment():
    """Serve the baseline capture setup page"""
    file_path = STATIC_DIR / 'baseline_capture.html'
    return send_file(file_path)

# Results routes
@assessment_bp.route('/results/core/<user_id>')
def core_results(user_id):
    """Serve the Core assessment results page"""
    # Check if template exists in assessments directory first
    template_path = TEMPLATES_DIR / 'results_core.html'
    if template_path.exists():
        return render_template('assessments/results_core.html', user_id=user_id)
    else:
        # Fallback to static file with placeholder replacement
        file_path = STATIC_DIR / 'results_core.html'
        with open(file_path, 'r') as f:
            content = f.read()
            content = content.replace('{{USER_ID}}', user_id)
            return content

@assessment_bp.route('/results/advanced/<user_id>')
def advanced_results(user_id):
    """Serve the Advanced assessment results page"""
    # Check if template exists in assessments directory first
    template_path = TEMPLATES_DIR / 'results_advanced.html'
    if template_path.exists():
        return render_template('assessments/results_advanced.html', user_id=user_id)
    else:
        # Fallback to static file with placeholder replacement
        file_path = STATIC_DIR / 'results_advanced.html'
        with open(file_path, 'r') as f:
            content = f.read()
            content = content.replace('{{USER_ID}}', user_id)
            return content

# API routes
@assessment_bp.route('/api/results/core/<user_id>')
def get_core_results(user_id):
    """Get Core assessment results data"""
    try:
        file_path = RESULTS_DIR / 'core' / f'{user_id}.json'
        with open(file_path, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({'error': 'User results not found', 'user_id': user_id}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid results data', 'user_id': user_id}), 500

@assessment_bp.route('/api/results/advanced/<user_id>')
def get_advanced_results(user_id):
    """Get Advanced assessment results data"""
    try:
        file_path = RESULTS_DIR / 'advanced' / f'{user_id}.json'
        with open(file_path, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({'error': 'User results not found', 'user_id': user_id}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid results data', 'user_id': user_id}), 500

@assessment_bp.route('/api/quiz/questions/<section>')
def get_questions(section):
    """Get questions for a specific section"""
    question_files = {
        'crt': 'assessments/core_4min/sections/cognitive_reflection/questions_simple.json',
        'aot': 'assessments/core_4min/sections/actively_open_minded/questions_simple.json',
        'listening': 'assessments/advanced_6min/sections/listening_preferences/questions.json',
        'relationship': 'assessments/advanced_6min/sections/relationship_style/questions.json'
    }
    
    if section in question_files:
        file_path = Path(question_files[section])
        with open(file_path, 'r') as f:
            return jsonify(json.load(f))
    
    return jsonify({'error': 'Section not found'}), 404

@assessment_bp.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """Submit quiz responses"""
    data = request.get_json()
    
    # Add timestamp
    data['timestamp'] = datetime.now().isoformat()
    
    # Determine assessment type and user ID
    assessment_type = data.get('assessmentType', 'unknown')
    user_id = data.get('userId', 'anonymous')
    
    # Save to user-specific results file
    try:
        if assessment_type in ['core', 'advanced']:
            # Ensure directory exists
            results_dir = RESULTS_DIR / assessment_type
            results_dir.mkdir(parents=True, exist_ok=True)
            
            user_filename = results_dir / f'{user_id}.json'
            with open(user_filename, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Fallback to old timestamp-based naming for unknown types
            results_dir = RESULTS_DIR
            results_dir.mkdir(parents=True, exist_ok=True)
            
            filename = results_dir / f'response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        
        save_success = True
        error_message = None
    except Exception as e:
        save_success = False
        error_message = str(e)
    
    # Note: Scoring is now handled by the assessment_transformer module
    # which calculates scores when data comes from Flask tests
    
    # Check if scores are included in the data (from direct API submissions)
    if 'scores' not in data and 'testId' in data:
        # Calculate scores for direct API submissions
        test_id = data.get('testId', '')
        answer_dict = {}
        if 'responses' in data:
            for key, value in data['responses'].items():
                answer_dict[key] = value.get('answer') if isinstance(value, dict) else value
        
        scoring_data = calculate_assessment_scores(test_id, answer_dict)
        data['scores'] = scoring_data
        
        # Add CRT score at top level for backward compatibility
        if 'crtScore' in scoring_data:
            data['crtScore'] = scoring_data['crtScore']
        
        # Re-save with scores
        try:
            if assessment_type in ['core', 'advanced']:
                user_filename = RESULTS_DIR / assessment_type / f'{user_id}.json'
                with open(user_filename, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error re-saving data with scores: {e}")
    
    # Return response based on quiz type
    if 'quiz_type' in data and data['quiz_type'] == 'crt' and 'crtScore' in data:
        crt_score = data['crtScore']
        return jsonify({
            'success': save_success,
            'status': 'success' if save_success else 'error',
            'user_id': user_id,
            'timestamp': data['timestamp'],
            'score': crt_score.get('score', 0),
            'total': crt_score.get('total', 3),
            'message': f'You got {crt_score.get("score", 0)} out of {crt_score.get("total", 3)} correct!' if save_success else f'Quiz completed but save failed: {error_message}',
            'error': error_message if not save_success else None
        })
    
    # Standard response for assessment submissions
    if save_success:
        return jsonify({
            'success': True,
            'status': 'success',
            'user_id': user_id,
            'timestamp': data['timestamp'],
            'message': 'Assessment saved successfully'
        })
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'user_id': user_id,
            'timestamp': data['timestamp'],
            'message': f'Assessment completed but save failed: {error_message}',
            'error': error_message
        }), 500

# Static file serving for JavaScript files
@assessment_bp.route('/assessments/static/<path:filename>')
def serve_assessment_static(filename):
    """Serve assessment static files"""
    return send_from_directory(str(STATIC_DIR), filename)

# Health check
@assessment_bp.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})