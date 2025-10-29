"""
Transform Flask test session data to Assessment format
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import Dict, List, Any
from src.utils.scoring import calculate_assessment_scores

def transform_flask_to_assessment(flask_session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Flask test session data to Assessment format for quiz submission.
    
    Args:
        flask_session: Flask test session data containing answers
        
    Returns:
        Assessment-formatted data ready for saving
    """
    # Use session_id as user_id for assessment
    user_id = flask_session.get('session_id', 'anonymous')
    test_id = flask_session.get('test_id', 'unknown')
    
    # Determine assessment type based on test_id
    assessment_type = determine_assessment_type(test_id)
    
    # Transform answers to assessment response format
    responses = {}
    sections = {}
    
    for answer in flask_session.get('answers', []):
        question_id = answer.get('question_id')
        answer_value = answer.get('answer')
        
        # Map question_id to assessment section and key
        section, key = map_question_to_assessment(question_id, test_id)
        
        if section and key:
            if section not in sections:
                sections[section] = {}
            
            sections[section][key] = {
                'answer': answer_value,
                'confidence': 'medium',  # Default confidence
                'time_taken': answer.get('time_taken', 0),
                'timestamp': answer.get('timestamp', datetime.now()).isoformat()
            }
    
    # Build assessment data structure
    assessment_data = {
        'userId': user_id,
        'assessmentType': assessment_type,
        'timestamp': datetime.now().isoformat(),
        'sessionId': flask_session.get('session_id'),
        'testId': test_id,
        'sections': sections,
        'responses': flatten_sections(sections),
        'totalQuestions': flask_session.get('total_questions', len(flask_session.get('answers', []))),
        'questionsAnswered': len(flask_session.get('answers', [])),
        'duration': flask_session.get('duration_seconds', 0)
    }
    
    return assessment_data

def generate_assessment_data(test_session: Dict[str, Any], assessment_type: str = 'core') -> Dict[str, Any]:
    """
    Generate assessment data structure compatible with quiz submission.
    
    Args:
        test_session: Flask test session data
        assessment_type: Type of assessment ('core' or 'advanced')
        
    Returns:
        Assessment data ready for submission
    """
    # Transform the session data
    assessment_data = transform_flask_to_assessment(test_session)
    
    # Override assessment type if specified
    assessment_data['assessmentType'] = assessment_type
    
    # Add quiz_type for specific assessments
    test_id = test_session.get('test_id', '')
    if 'crt' in test_id.lower():
        assessment_data['quiz_type'] = 'crt'
    
    # Calculate scores for the assessment
    # Create a simple answer dict from the Flask answers
    answer_dict = {}
    for answer in test_session.get('answers', []):
        question_id = str(answer.get('question_id'))
        answer_dict[question_id] = answer.get('answer')
    
    # Calculate scores
    scoring_data = calculate_assessment_scores(test_id, answer_dict)
    
    # Add scores to assessment data
    assessment_data['scores'] = scoring_data
    
    # Also add CRT score at top level for backward compatibility
    if 'crtScore' in scoring_data:
        assessment_data['crtScore'] = scoring_data['crtScore']
    
    return assessment_data

def determine_assessment_type(test_id: str) -> str:
    """
    Determine assessment type based on test ID.
    
    Args:
        test_id: Flask test ID
        
    Returns:
        'core' or 'advanced' assessment type
    """
    test_id_lower = test_id.lower()
    
    # Map test IDs to assessment types
    if any(keyword in test_id_lower for keyword in ['core', 'crt', 'numeracy', 'aot', 'intent', 'nfc', 'anchoring']):
        return 'core'
    elif any(keyword in test_id_lower for keyword in ['advanced', 'emotion', 'listening', 'relationship', 'loss', 'perspective']):
        return 'advanced'
    else:
        # Default to core
        return 'core'

def map_question_to_assessment(question_id: str, test_id: str) -> tuple:
    """
    Map Flask question ID to assessment section and key.
    
    Args:
        question_id: Flask question ID
        test_id: Flask test ID
        
    Returns:
        Tuple of (section, key) or (None, None) if not mapped
    """
    # Example mapping logic - customize based on your test structure
    test_id_lower = test_id.lower()
    
    # CRT mapping
    if 'crt' in test_id_lower:
        if 'bat' in question_id.lower() or 'q1' in question_id:
            return ('crt', 'bat_ball')
        elif 'widget' in question_id.lower() or 'q2' in question_id:
            return ('crt', 'widget')
        elif 'lily' in question_id.lower() or 'q3' in question_id:
            return ('crt', 'lily_pad')
    
    # AOT mapping
    elif 'aot' in test_id_lower:
        return ('aot', question_id)
    
    # Numeracy mapping
    elif 'numeracy' in test_id_lower:
        return ('numeracy', question_id)
    
    # Intent attribution mapping
    elif 'intent' in test_id_lower:
        return ('intent', question_id)
    
    # Need for closure mapping
    elif 'nfc' in test_id_lower:
        return ('nfc', question_id)
    
    # Anchoring mapping
    elif 'anchoring' in test_id_lower:
        return ('anchoring', question_id)
    
    # Default mapping
    return ('general', question_id)

def flatten_sections(sections: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Flatten nested sections into a single responses object.
    
    Args:
        sections: Nested sections dictionary
        
    Returns:
        Flattened responses dictionary
    """
    responses = {}
    
    for section, questions in sections.items():
        for question_key, question_data in questions.items():
            # Create flattened key
            flat_key = f"{section}_{question_key}" if section != 'general' else question_key
            responses[flat_key] = question_data
    
    return responses